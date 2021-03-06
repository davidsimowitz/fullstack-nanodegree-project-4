import contextlib
import datetime
import flask
import functools
import hashlib
import httplib2
import json
import logging
import logging.config
import logging.handlers
import oauth2client.client
import os
import random
import re
import requests
import sqlalchemy
import string
import sys


APPLICATION_PATH = '/var/www/flask/coordinate/'
CLIENT_SECRETS_FILE = 'client_secret.json'


if os.path.exists(APPLICATION_PATH):
    try:
        sys.path.insert(1, APPLICATION_PATH)
        import models
    except (ModuleNotFoundError, ImportError, PermissionError) as err:
        raise


try:
    CLIENT_ID = json.loads(
        open(APPLICATION_PATH + CLIENT_SECRETS_FILE, 'r').read()
        )['web']['client_id']
except (FileNotFoundError, IsADirectoryError, PermissionError) as err:
    raise


app = flask.Flask(__name__)

engine = sqlalchemy.create_engine(models.DB)
models.declarative_base.metadata.bind = engine
create_sqlalchemy_session = sqlalchemy.orm.sessionmaker(bind=engine)


@contextlib.contextmanager
def db_session():
    db = create_sqlalchemy_session()
    try:
        yield db
    except (sqlalchemy.exc.DBAPIError, sqlalchemy.exc.SQLAlchemyError) as err:
        # database error encountered
        db.rollback()
        raise
    finally:
        db.close()


def login_required(func):
    @functools.wraps(func)
    def decorated_function(*args, **kwargs):
        if 'username' not in flask.session:
            return flask.redirect('/login/')
        else:
            return func(*args, **kwargs)
    return decorated_function


def url_trace(func):
    @functools.wraps(func)
    def decorated_function(*args, **kwargs):
        if 'current_page' in flask.session:
            flask.session['previous_page'] = flask.session['current_page']
        flask.session['current_page'] = flask.request.full_path
        return func(*args, **kwargs)
    return decorated_function


def timestamp_gen(file_ext=False):
    """Timestamp generator.

    Generates a str representation of the current UTC time.

    Args:
        file_ext: Set to True to return the current UTC time in ISO 8601
            format <YYYY-MM-DD_HH:MM:SS.ssssss>. Defaults to False.

    Returns:
        Current UTC time in <Weekday Month DD HH:MM:SS YYYY>
        format, unless file_ext is set to True.

        Examples:
            'Sun Dec  3 20:30:18 2017' if file_ext is False.
            '2017-12-03_20:30:18.817695' if file_ext is True.
    """
    current_time = datetime.datetime.now()

    if file_ext:
        return current_time.isoformat('_')
    else:
        return current_time.ctime()


_MONTHS = 'january|february|march|april|may|june|july' \
          '|august|september|october|november|december'

month_to_int = {month: i for i, month in enumerate(_MONTHS.split('|'),
                                                   start=1)}


def parse_date(str_input):
    """Parses input and extracts date.

    Extracts date from input str.

    Args:
        str_input: str representation of date value.

    Returns:
        A dict mapping date keys to their corresponding values.

    Examples:
        str_input: 'November 23, 2017'
        returns: {'month': 'November', 'day': '23', 'year': '2017'}

        str_input: 'november 23 2017'
        returns: {'month': 'november', 'day': '23', 'year': '2017'}

        str_input: '2/3/2017'
        returns: {'month': '2', 'day': '3', 'year': '2017'}

        str_input: '2-3-2017'
        returns: {'month': '2', 'day': '3', 'year': '2017'}

        str_input: '02-03-2017'
        returns: {'month': '02', 'day': '03', 'year': '2017'}

    Dependencies:
        _MONTHS
        month_to_int
        re
    """
    # patterns = [
    #             YYYY_MM_DD ,
    #             MM_DD_YYYY ,
    #             MONTH_DD_YYYY
    #            ]
    patterns = [r'(?P<year>[\d]{4})[-/]?'
                r'(?P<month>[\d]{1,2})[-/]?'
                r'(?P<day>[\d]{1,2})',
                r'(?P<month>[\d]{1,2})[-/]?'
                r'(?P<day>[\d]{1,2})[-/]?'
                r'(?P<year>[\d]{4})',
                r'(?P<month>' + _MONTHS + r'){1}\s'
                r'(?P<day>[\d]{1,2})\,?\s(?P<year>[\d]{4})']

    for pattern in patterns:
        if re.match(pattern, str_input, re.IGNORECASE):
            return re.match(pattern, str_input, re.IGNORECASE).groupdict()


def parse_time(str_input):
    """Parses str input value and extracts time.

    Args:
        str_input: str representation of time value.

    Returns:
        A dict mapping time keys to their corresponding values.

    Examples:
        str_input: '7:00 AM'
        returns: {'minutes': '00', 'twelve_hr': 'AM', 'hours': '7'}

        str_input: '7:00 A.M.'
        returns: {'minutes': '00', 'twelve_hr': 'A.M.', 'hours': '7'}

        str_input: '7:00'
        returns: {'minutes': '00', 'hours': '7'}

        str_input: '07:00'
        returns: {'minutes': '00', 'hours': '07'}

        str_input: '5:00 pm'
        returns: {'minutes': '00', 'twelve_hr': 'pm', 'hours': '5'}

        str_input: '5:00 p.m.'
        returns: {'minutes': '00', 'twelve_hr': 'p.m.', 'hours': '5'}

        str_input: '17:00'
        returns: {'minutes': '00', 'hours': '17'}

    Dependencies:
        re
    """
    # patterns = [
    #             HH:MM:SS(+/-)TT:TT ,
    #             HH:MM:SS (AM/PM) ,
    #             HH:MM (AM/PM) ,
    #             HH:MM:SS (24-hour notation) ,
    #             HH:MM (24-hour notation)
    #            ]
    patterns = [r'(?P<hours>[\d]{1,2})[:]{1}'
                r'(?P<minutes>[\d]{2})[:]{1}'
                r'(?P<seconds>[\d]{2})'
                r'(?P<timezone>[+-]?[\d]{2}[:]{1}[\d]{2})',
                r'(?P<hours>[\d]{1,2})[:]{1}'
                r'(?P<minutes>[\d]{2})[:]{1}'
                r'(?P<seconds>[\d]{2})\s?'
                r'(?P<twelve_hr>am|pm|a\.m\.|p\.m\.){1}',
                r'(?P<hours>[\d]{1,2})[:]{1}'
                r'(?P<minutes>[\d]{2})\s?'
                r'(?P<twelve_hr>am|pm|a\.m\.|p\.m\.){1}',
                r'(?P<hours>[\d]{1,2})[:]{1}'
                r'(?P<minutes>[\d]{2})[:]{1}'
                r'(?P<seconds>[\d]{2})',
                r'(?P<hours>[\d]{1,2})[:]{1}'
                r'(?P<minutes>[\d]{2})']
    for pattern in patterns:
        if re.match(pattern, str_input, re.IGNORECASE):
            return re.match(pattern, str_input, re.IGNORECASE).groupdict()


def verify_date(date_dict):
    """Verifies value received and converts to an acceptable date format.

    Args:
        date_dict: Dictionary representation of a date value. Mandatory keys
            include 'year', 'month', and 'days'.
    Returns:
        A datetime.date object.

    Examples:
        date_dict: {'month': 'November', 'day': '23', 'year': '2017'}
        returns: datetime.date(2017, 11, 23)

        date_dict: {'month': 'november', 'day': '23', 'year': '2017'}
        returns: datetime.date(2017, 11, 23)

        date_dict: {'month': '2', 'day': '3', 'year': '2017'}
        returns: datetime.date(2017, 2, 3)

        date_dict: {'month': '02', 'day': '03', 'year': '2017'}
        returns: datetime.date(2017, 2, 3)

    Dependencies:
        datetime
    """
    try:
        date_dict['month'] = month_to_int[date_dict['month'].lower()]
    except KeyError:
        pass

    try:
        event_date = datetime.date(int(date_dict['year']),
                                   int(date_dict['month']),
                                   int(date_dict['day']))
    except (TypeError, ValueError) as err:
        return None
    else:
        return event_date


def verify_time(time_dict):
    """Verifies value received and converts to an acceptable time format.

    Args:
        time_dict: Dictionary representation of a time value. Mandatory keys
            include 'hours' and 'minutes'. The 'twelve_hr' key is only needed
            if the 'hours' value is in 12-hour-notation.
    Returns:
        A datetime.time object that includes hours and minutes.

    Examples:
        time_dict: {'minutes': '00', 'twelve_hr': 'AM', 'hours': '7'}
        returns: datetime.time(7, 0)

        time_dict: {'minutes': '00', 'twelve_hr': 'A.M.', 'hours': '7'}
        returns: datetime.time(7, 0)

        time_dict: {'minutes': '00', 'hours': '7'}
        returns: datetime.time(7, 0)

        time_dict: {'minutes': '00', 'hours': '07'}
        returns: datetime.time(7, 0)

        time_dict: {'minutes': '00', 'twelve_hr': 'pm', 'hours': '5'}
        returns: datetime.time(17, 0)

        time_dict: {'minutes': '00', 'twelve_hr': 'p.m.', 'hours': '5'}
        returns: datetime.time(17, 0)

        time_dict: {'minutes': '00', 'hours': '17'}
        returns: datetime.time(17, 0)

    Dependencies:
        datetime
    """
    try:
        time_dict['hours'] = int(time_dict['hours'])
        time_dict['minutes'] = int(time_dict['minutes'])
        time_dict['seconds'] = int(time_dict['seconds'])
    except KeyError:
        pass

    try:
        if time_dict['twelve_hr'].lower()[0] is 'p':
            time_dict['hours'] = time_dict['hours'] + 12
    except KeyError:
        pass

    try:
        event_time = datetime.time(hour=time_dict['hours'],
                                   minute=time_dict['minutes'])
    except (TypeError, ValueError) as err:
        return None
    else:
        return event_time


def date_checker(date):
    """Authenticates date value.

    Args:
        date: A str representation of a date value.

    Returns:
        A datetime.date object if input date is a valid date. Else, None.

    Dependencies:
        parse_date()
        verify_date()
    """
    date = parse_date(date)
    date = verify_date(date)

    return date


def time_checker(time):
    """Authenticates time value.

    Args:
        time: A str representation of a time value.

    Returns:
        A datetime.time object if input time is a valid time. Else, None.

    Dependencies:
        parse_time()
        verify_time()
    """
    time = parse_time(time)
    time = verify_time(time)

    return time


def set_event_fields(event):
    """Set or update Event object fields.

    Use in a POST method to return an updated Event object. Event
    fields will be updated from str values pulled from form data.

    Args:
        event: Event object.

    Returns:
        valid: Boolean representing whether the event has valid values.
        messages: A lookup table mapping event fields to error messages if
                  values are not valid.
        event: Updated Event object.

    Dependencies:
        models.Event
        date_checker()
        time_checker()
    """
    valid = True
    messages = dict()

    # determine start/end dates based on available input.
    start_date, end_date = None, None

    if flask.request.form['start_date']:
        start_date = flask.request.form['start_date']
        start_date = date_checker(start_date)
        if not start_date:
            messages['date'] = "date is invalid"

    if flask.request.form['end_date']:
        end_date = flask.request.form['end_date']
        end_date = date_checker(end_date)
        if not end_date:
            messages['date'] = "date is invalid"

    if start_date and end_date:
        if start_date <= end_date:
            event.start_date, event.end_date = start_date, end_date
        else:
            event.start_date, event.end_date = None, None
            messages['date'] = "ending date cannot occur before starting date"
            valid = False
    elif start_date:
        end_date = start_date
        event.start_date, event.end_date = start_date, end_date
    elif end_date:
        start_date = end_date
        event.start_date, event.end_date = start_date, end_date
    else:
        messages['date'] = "date is required"
        valid = False

    # determine start/end times based on available input.
    start_time, end_time = None, None

    if flask.request.form['start_time']:
        start_time = flask.request.form['start_time']
        start_time = time_checker(start_time)
        if not start_time:
            messages['time'] = "time is invalid"

    if flask.request.form['end_time']:
        end_time = flask.request.form['end_time']
        end_time = time_checker(end_time)
        if not end_time:
            messages['time'] = "time is invalid"

    if start_date and end_date and start_date == end_date:
        if start_time and end_time and start_time <= end_time:
            event.start_time, event.end_time = start_time, end_time
        elif start_time and end_time and start_time > end_time:
            event.start_time, event.end_time = None, None
            messages['time'] = "ending time cannot occur before starting time"
            valid = False
        else:
            event.start_time, event.end_time = start_time, end_time
    else:
        event.start_time, event.end_time = start_time, end_time

    if flask.request.form['name']:
        event.name = flask.request.form['name']
    else:
        messages['name'] = "name is required"
        valid = False

    if flask.request.form['description']:
        event.description = flask.request.form['description']
    elif valid:
        event.description = 'please add a description'

    return valid, messages, event


def set_activity_fields(activity):
    """Set or update Activity object fields.

    Use in a POST method to return an updated Activity object. Activity
    fields will be updated from str values pulled from form data.

    Args:
        activity: Activity object.

    Returns:
        valid: Boolean representing whether the activity has valid values.
        messages: A lookup table mapping activity fields to error messages if
                  values are not valid.
        activity: Updated Activity object.

    Dependencies:
        models.Activity
        models.icon_list()
    """
    valid = True
    messages = dict()

    if flask.request.form['name']:
        activity.name = flask.request.form['name']
    else:
        messages['name'] = "name is required"
        valid = False

    if flask.request.form['icon']:
        # verify valid icon selection
        if flask.request.form['icon'] == "/static/img/placeholder-logo.svg":
            messages['icon'] = 'icon is required'
            valid = False
        elif flask.request.form['icon'] in models.icon_list():
            activity.icon = flask.request.form['icon']
        else:
            messages['icon'] = 'selected icon is invalid'
            valid = False
    else:
        messages['icon'] = 'icon is required'
        valid = False

    return valid, messages, activity


@app.route('/')
@app.route('/activities/')
@url_trace
def display_activities():
    """Display all Activity records from DB"""
    with db_session() as db:
        activities = db.query(models.Activity)
    return flask.render_template('activities.html',
                                 activities=activities)


@app.route('/login/')
def user_login():
    """Create an anti-forgery state token and store it in the session"""
    state = hashlib.sha256(os.urandom(1024)).hexdigest()
    flask.session['state'] = state

    if 'previous_page' not in flask.session:
        flask.session['previous_page'] = '/'

    google_oauth_2_0 = (
        "//ajax.googleapis.com/ajax/libs/jquery/1.8.2/jquery.min.js",
        "//apis.google.com/js/platform.js?onload=init")

    return flask.render_template('login.html',
                                 STATE=state,
                                 redirect_to=flask.session['previous_page'],
                                 load_scripts=(google_oauth_2_0),
                                 back=flask.session['previous_page'])


@app.route('/logout/')
@url_trace
def user_logout():
    """Logout user"""
    try:
        oauth_provider = flask.session['oauth_provider']
    except KeyError:
        response = flask.make_response(
                     json.dumps('current user not logged in'),
                     401)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        if oauth_provider == 'google':
            return flask.redirect(flask.url_for('google_disconnect'))
        elif oauth_provider == 'facebook':
            return flask.redirect(flask.url_for('facebook_disconnect'))


def validate_state_token(*, session=flask.session):
    """Authenticate a session's state token"""
    # Validate state token
    if flask.request.args.get('state') != flask.session['state']:
        response = flask.make_response(
                       json.dumps('invalid state parameter'),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return (False, response)
    else:
        return (True, None)


def login_splash_page(*, picture):
    """Display login splash page"""
    return ('<img src="{}" id="login-image">'.format(flask.session['picture']))


@app.route('/google.connect/', methods=['POST'])
def google_connect():
    """OAuth via Google"""
    validated, response = validate_state_token()
    if not validated:
        return response

    # Obtain authorization code
    code = flask.request.data

    try:
        # Create flow from a clientsecrets file
        oauth_flow = oauth2client.client.flow_from_clientsecrets(
                         '/var/www/flask/coordinate/client_secret.json',
                         scope=['email', 'openid'],
                         redirect_uri='postmessage')
        # Exchange authorization code for a Credentials object
        credentials = oauth_flow.step2_exchange(code)
    except oauth2client.client.InvalidClientSecretsError:
        # Format of ClientSecrets file is invalid.
        response = flask.make_response(
                       json.dumps(('format of ClientSecrets'
                                   ' file is invalid')),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return response
    except oauth2client.client.FlowExchangeError:
        # Error trying to exchange an authorization grant for an access token.
        response = flask.make_response(
                       json.dumps(('error trying to exchange'
                                   ' an authorization grant'
                                   ' for an access token')),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?'
           'access_token={}'.format(access_token))
    http = httplib2.Http()
    result = json.loads(str(http.request(url, 'GET')[1], 'utf-8'))

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = flask.make_response(
                       json.dumps(result.get('error')),
                       500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    google_account_id = credentials.id_token['sub']
    if result['user_id'] != google_account_id:
        response = flask.make_response(
                       json.dumps(("token's user ID does not"
                                   " match given user ID")),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = flask.make_response(
                       json.dumps("token's client ID does not match app's"),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = flask.session.get('access_token')
    stored_google_account_id = flask.session.get('google_account_id')
    if (stored_access_token is not None and
            google_account_id == stored_google_account_id):
        response = flask.make_response(
                       json.dumps('current user is already connected'),
                       200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    flask.session['access_token'] = credentials.access_token
    flask.session['google_account_id'] = google_account_id

    # Get user info
    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    flask.session['oauth_provider'] = 'google'
    flask.session['username'] = data['name']
    flask.session['picture'] = data['picture']
    flask.session['email'] = data['email']

    # Add new user if not already in system
    user_id = get_user_id(user_email=flask.session['email'])
    if not user_id:
        user_id = make_user(session=flask.session)
    flask.session['user_id'] = user_id

    return login_splash_page(picture=flask.session['picture']) + \
        flask.session['username']


@app.route('/google.disconnect/')
def google_disconnect():
    """Disconnect a login session that was setup with Google"""
    access_token = flask.session.get('access_token')
    if access_token is None:
        response = flask.make_response(
                     json.dumps('current user not connected'),
                     401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = ('https://accounts.google.com/o/oauth2/revoke?'
           'token={}'.format(flask.session['access_token']))
    http = httplib2.Http()
    result = http.request(url, 'GET')[0]

    if result['status'] == '200':

        if 'previous_page' in flask.session:
            redirect_url = flask.session['previous_page']
        else:
            redirect_url = '/'

        del flask.session['oauth_provider']
        del flask.session['access_token']
        del flask.session['google_account_id']
        del flask.session['username']
        del flask.session['email']
        del flask.session['picture']
        del flask.session['previous_page']
        del flask.session['current_page']

        response = flask.make_response(
                       json.dumps('successfully disconnected'),
                       200)
        response.headers['Content-Type'] = 'application/json'
        return flask.redirect(redirect_url)
    else:
        response = flask.make_response(
                       json.dumps('failed to revoke token for given user'),
                       400)
        response.headers['Content-Type'] = 'application/json'
        return flask.redirect('/')


@app.route('/facebook.connect/', methods=['POST'])
def facebook_connect():
    """OAuth via Facebook"""
    validated, response = validate_state_token()
    if not validated:
        return response

    # Obtain short-lived access token and decode from bytes
    access_token = str(flask.request.data, 'utf-8')

    # Construct url to request long-lived token from Facebook
    fb_client_secret = json.loads(open('fb_client_secret.json', 'r').read())
    app_id = fb_client_secret['web']['app_id']
    app_secret = fb_client_secret['web']['app_secret']
    url = ('https://graph.facebook.com/oauth/access_token?'
           'grant_type=fb_exchange_token&client_id={}&client_secret={}&'
           'fb_exchange_token={}'.format(app_id, app_secret, access_token))

    try:
        # Request long-lived token from Facebook.
        http = httplib2.Http()
        http_response, http_content = http.request(url, 'GET')

        # Convert from bytes to str to Python object.
        result = json.loads(str(http_content, 'utf-8'))
    except json.decoder.JSONDecodeError:
        # Exception converting http_content to Python object.
        response = flask.make_response(
                       json.dumps(('format of ``str`` instance containing'
                                   ' a JSON document is invalid')),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return response
    except httplib2.RelativeURIError:
        response = flask.make_response(
            json.dumps('format of Facebook exchange token URL is invalid'),
            401)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        if result.get('access_token'):
            token = result['access_token']
        else:
            # Error exchanging short-lived token for a long-lived token.
            response = flask.make_response(
                           json.dumps(('error trying to exchange a'
                                       ' short-lived access token for'
                                       ' a long-lived access token')),
                           500)
            response.headers['Content-Type'] = 'application/json'
            return response

    # Get user info
    url = ('https://graph.facebook.com/v2.11/me?'
           'access_token={}&fields=name,id,email'.format(token))
    http = httplib2.Http()
    result = str(http.request(url, 'GET')[1], 'utf-8')

    data = json.loads(result)
    flask.session['oauth_provider'] = 'facebook'
    flask.session['username'] = data["name"]
    flask.session['email'] = data["email"]
    flask.session['facebook_id'] = data["id"]

    # Get user picture
    url = ('https://graph.facebook.com/v2.11/me/picture?'
           'access_token={}&redirect=0&height=200&width=200'.format(token))
    http = httplib2.Http()
    result = str(http.request(url, 'GET')[1], 'utf-8')
    data = json.loads(result)
    flask.session['picture'] = data["data"]["url"]

    # The token must be stored in the login_session in order to properly logout
    flask.session['access_token'] = token

    # Add new user if not already in system
    user_id = get_user_id(user_email=flask.session['email'])
    if not user_id:
        user_id = make_user(session=flask.session)
    flask.session['user_id'] = user_id

    return login_splash_page(picture=flask.session['picture'])


@app.route('/facebook.disconnect/')
def facebook_disconnect():
    """Disconnect a login session that was setup with Facebook"""
    facebook_id = flask.session.get('facebook_id')
    if facebook_id is None:
        response = flask.make_response(
                       json.dumps('current user not connected'),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = ('https://graph.facebook.com/{}/permissions?'
           'access_token={}'.format(facebook_id,
                                    flask.session['access_token']))
    http = httplib2.Http()
    result = json.loads(str(http.request(url, 'DELETE')[1], 'utf-8'))

    logged_out = result.get('success')
    if logged_out:
        del flask.session['oauth_provider']
        del flask.session['access_token']
        del flask.session['facebook_id']
        del flask.session['username']
        del flask.session['email']
        del flask.session['picture']
        del flask.session['previous_page']
        del flask.session['current_page']

        response = flask.make_response(
                     json.dumps('successfully disconnected'),
                     200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = flask.make_response(
                     json.dumps('failed to revoke token for given user'),
                     400)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/activities/<int:activity_id>/')
@app.route('/activities/<int:activity_id>/events/')
@url_trace
def display_activity(activity_id):
    """Display Activity record from DB with matching activity_id.

    Display Activity and list all Event records corresponding to it
    in date order.
    """
    hosting, attending, considering = None, None, None
    # User login required for hosting/attending/considering status
    if 'username' in flask.session:
        hosting = hosting_events()
        attending = attending_events()
        considering = considering_events()

    with db_session() as db:
        activity = db.query(models.Activity) \
                     .filter_by(id=activity_id) \
                     .one()
        dates = db.query(
                      models.Event,
                      sqlalchemy.func.generate_series(
                          models.Event.start_date,
                          models.Event.end_date,
                          sqlalchemy.text("'1 day'::interval")
                          )
                      .cast(sqlalchemy.Date)
                      .label('event_date')
                      ) \
                  .subquery()
        events = db.query(
                       models.Event,
                       models.Event.id,
                       models.Event.name,
                       models.Event.description,
                       models.Event.start_date,
                       models.Event.end_date,
                       models.Event._start_time,
                       models.Event._end_time,
                       models.Event.user_id,
                       models.Event.activity_id,
                       sqlalchemy.func.to_char(
                                          dates.c.event_date,
                                          sqlalchemy.text(
                                              "'FMDay, FMMonth FMDD, FMYYYY'"
                                              )
                                          )
                       .label('date'),
                       sqlalchemy.func.to_char(
                                          models.Event._start_time,
                                          sqlalchemy.text(
                                              "'FMHH12:MI pm'"
                                              )
                                          )
                       .label('start_time'),
                       sqlalchemy.func.to_char(models.Event._end_time,
                                               sqlalchemy.text(
                                                   "'FMHH12:MI pm'"
                                                   )
                                               )
                       .label('end_time'),
                       dates) \
                   .join(dates, models.Event.id == dates.c.id) \
                   .filter_by(activity_id=activity.id) \
                   .order_by(dates.c.event_date.asc(),
                             models.Event._start_time.asc(),
                             models.Event._end_time.asc()) \
                   .filter(dates.c.event_date >= datetime.date.today()) \
                   .all()

    return flask.render_template('events.html',
                                 activity=activity,
                                 events=events,
                                 hosting=hosting,
                                 attending=attending,
                                 considering=considering,
                                 user_id=get_user_id(
                                     user_email=flask.session.get('email', 0)
                                     ),
                                 back=flask.url_for('display_activities'))


@app.route('/activities/new/', methods=['GET', 'POST'])
@url_trace
@login_required
def make_activity():
    """Create new Activity record in DB"""
    if flask.request.method == 'POST':
        new_activity = models.Activity(
                           user_id=get_user_id(
                                       user_email=flask.session['email']))
        valid, messages, new_activity = set_activity_fields(new_activity)
        if not valid:
            icons = models.icon_list()
            return flask.render_template('new-activity.html',
                                         previous=new_activity,
                                         error_msg=messages,
                                         icons=icons)
        with db_session() as db:
            db.add(new_activity)
            db.commit()

            return flask.redirect(
                       flask.url_for(
                           'display_activity',
                           activity_id=new_activity.id))
    else:
        icons = models.icon_list()
        return flask.render_template('new-activity.html',
                                     icons=icons)


@app.route('/activities/<int:activity_id>/edit/', methods=['GET', 'POST'])
@url_trace
@login_required
def update_activity(activity_id):
    """Update Activity record in DB with matching activity_id"""
    with db_session() as db:
        activity = db.query(models.Activity) \
                     .filter_by(id=activity_id) \
                     .one()

    # Activity can only be edited by its owner
    if activity.user_id != get_user_id(user_email=flask.session['email']):
        return flask.redirect(
                   flask.url_for('display_activity',
                                 activity_id=activity.id))

    if flask.request.method == 'POST':
        valid, messages, edited_activity = set_activity_fields(activity)
        if not valid:
            icons = models.icon_list()
            return flask.render_template('edit-activity.html',
                                         activity=edited_activity,
                                         error_msg=messages,
                                         icons=icons)
        with db_session() as db:
            db.add(edited_activity)
            db.commit()

            return flask.redirect(
                       flask.url_for('display_activity',
                                     activity_id=edited_activity.id))
    else:
        icons = models.icon_list()
        return flask.render_template('edit-activity.html',
                                     activity=activity,
                                     icons=icons)


@app.route('/activities/<int:activity_id>/delete/', methods=['GET', 'POST'])
@url_trace
@login_required
def delete_activity(activity_id):
    """Delete Activity record in DB with matching activity_id"""
    with db_session() as db:
        activity = db.query(models.Activity) \
                     .filter_by(id=activity_id) \
                     .one()

    # Activity can only be deleted by its owner
    if activity.user_id != get_user_id(user_email=flask.session['email']):
        return flask.redirect(
                   flask.url_for('display_activity',
                                 activity_id=activity.id))

    if flask.request.method == 'POST':
        with db_session() as db:
            events = db.query(models.Event) \
                       .filter_by(activity_id=activity_id) \
                       .all()
        if events:
            error_msg = ('Activity cannot be deleted, events '
                         'are associated with this activity.')
            return flask.render_template('delete-activity.html',
                                         activity=activity,
                                         error_msg=error_msg)
        else:
            with db_session() as db:
                db.delete(activity)
                db.commit()
            return flask.redirect(
                       flask.url_for('display_activities'))

    else:
        return flask.render_template('delete-activity.html',
                                     activity=activity)


@app.route('/activities/<int:activity_id>/events/<int:event_id>/')
@url_trace
def display_event(activity_id, event_id):
    """Display Event record from DB with matching event_id"""
    with db_session() as db:
        activity = db.query(models.Activity) \
                     .filter_by(id=activity_id) \
                     .one()
        event = db.query(models.Event,
                         models.Event.id,
                         models.Event.name,
                         models.Event.description,
                         models.Event.start_date,
                         models.Event.end_date,
                         models.Event.user_id,
                         models.Event.activity_id,
                         sqlalchemy.func.to_char(
                                            models.Event.start_date,
                                            sqlalchemy.text(
                                                "'FMDay, FMMonth FMDD, FMYYYY'"
                                                )
                                            )
                         .label('starting_date'),
                         sqlalchemy.func.to_char(
                                            models.Event.start_date,
                                            sqlalchemy.text(
                                                "'FMMon FMDDth'"
                                                )
                                            )
                         .label('abbr_starting_date'),
                         sqlalchemy.func.to_char(
                                            models.Event.start_date,
                                            sqlalchemy.text(
                                                "'FMDy, FMMon FMDDth'"
                                                )
                                            )
                         .label('abbr_starting_day'),
                         sqlalchemy.func.to_char(
                                            models.Event.end_date,
                                            sqlalchemy.text(
                                                "'FMDay, FMMonth FMDD, FMYYYY'"
                                                )
                                            )
                         .label('ending_date'),
                         sqlalchemy.func.to_char(
                                            models.Event.end_date,
                                            sqlalchemy.text(
                                                "'FMMon FMDDth'"
                                                )
                                            )
                         .label('abbr_ending_date'),
                         sqlalchemy.func.to_char(
                                            models.Event.end_date,
                                            sqlalchemy.text(
                                                "'FMDy, FMMon FMDDth'"
                                                )
                                            )
                         .label('abbr_ending_day'),
                         sqlalchemy.func.to_char(
                                            models.Event._start_time,
                                            sqlalchemy.text(
                                                "'FMHH12:MI pm'"
                                                )
                                            )
                         .label('start_time'),
                         sqlalchemy.func.to_char(
                                            models.Event._end_time,
                                            sqlalchemy.text(
                                                "'FMHH12:MI pm'"
                                                )
                                            )
                         .label('end_time')
                         ) \
                  .filter_by(id=event_id,
                             activity_id=activity_id) \
                  .one()
        is_hosting = db.query(models.Hosting) \
                       .filter(
                         sqlalchemy.and_(
                           models.Hosting.event_id == event.id,
                           models.Hosting.user_id ==
                           get_user_id(
                                   user_email=flask.session.get('email', 0)
                                   )
                           )
                        ) \
                       .first()
    return flask.render_template('event.html',
                                 activity=activity,
                                 event=event,
                                 user_id=get_user_id(
                                     user_email=flask.session.get('email', 0)
                                     ),
                                 hosting=is_hosting,
                                 back=flask.url_for('display_activity',
                                                    activity_id=activity.id))


@app.route('/activities/<int:activity_id>/events/new/',
           methods=['GET', 'POST'])
@url_trace
@login_required
def make_event(activity_id):
    """Create new Event record in DB"""
    if flask.request.method == 'POST':
        new_event = models.Event(name=flask.request.form['name'],
                                 activity_id=activity_id,
                                 user_id=get_user_id(
                                             user_email=flask.session['email']
                                         )
                                 )
        valid, messages, new_event = set_event_fields(new_event)
        if not valid:
            with db_session() as db:
                activity = db.query(models.Activity) \
                             .filter_by(id=activity_id) \
                             .one()
            return flask.render_template('new-event.html',
                                         activity=activity,
                                         previous=new_event,
                                         error_msg=messages)
        with db_session() as db:
            db.add(new_event)
            db.commit()
            hosting = models.Hosting(event_id=new_event.id,
                                     user_id=get_user_id(
                                             user_email=flask.session['email']
                                             )
                                     )
            db.add(hosting)
            db.commit()
            return flask.redirect(
                       flask.url_for('display_event',
                                     activity_id=activity_id,
                                     event_id=new_event.id))
    else:
        with db_session() as db:
            activity = db.query(models.Activity) \
                         .filter_by(id=activity_id) \
                         .one()
        return flask.render_template('new-event.html',
                                     activity=activity)


@app.route('/activities/<int:activity_id>/events/<int:event_id>/edit/',
           methods=['GET', 'POST'])
@url_trace
@login_required
def update_event(activity_id, event_id):
    """Update Event record in DB with matching event_id"""
    with db_session() as db:
        activity = db.query(models.Activity) \
                     .filter_by(id=activity_id) \
                     .one()
        event = db.query(models.Event) \
                  .filter_by(id=event_id,
                             activity_id=activity_id) \
                  .one()

    # Event can only be edited by its owner
    if event.user_id != get_user_id(user_email=flask.session['email']):
        return flask.redirect(
                   flask.url_for('display_event',
                                 activity_id=activity.id,
                                 event_id=event.id))

    if flask.request.method == 'POST':
        valid, messages, edited_event = set_event_fields(event)
        if not valid:
            return flask.render_template('edit-event.html',
                                         activity=activity,
                                         event=edited_event,
                                         error_msg=messages)

        with db_session() as db:
            db.add(edited_event)
            db.commit()
            return flask.redirect(
                       flask.url_for('display_event',
                                     activity_id=activity_id,
                                     event_id=edited_event.id))
    else:
        return flask.render_template('edit-event.html',
                                     activity=activity,
                                     event=event)


@app.route('/activities/<int:activity_id>/events/<int:event_id>/delete/',
           methods=['GET', 'POST'])
@url_trace
@login_required
def delete_event(activity_id, event_id):
    """Delete Event record in DB with matching event_id"""
    with db_session() as db:
        activity = db.query(models.Activity) \
                     .filter_by(id=activity_id) \
                     .one()
        event = db.query(models.Event) \
                  .filter_by(id=event_id,
                             activity_id=activity_id) \
                  .one()
        hosting = db.query(models.Hosting) \
                    .filter_by(event_id=event.id) \
                    .first()

    # Event can only be deleted by its owner
    if event.user_id != get_user_id(user_email=flask.session['email']):
        return flask.redirect(
                   flask.url_for('display_event',
                                 activity_id=activity.id,
                                 event_id=event.id))

    if flask.request.method == 'POST':
        with db_session() as db:
            delete_attendings = db.query(models.Attending) \
                                  .filter(
                                      models.Attending.event_id == event.id
                                      ) \
                                  .delete(synchronize_session='fetch')
            delete_considerings = db.query(models.Considering) \
                                    .filter(
                                        models.Considering.event_id == event.id
                                        ) \
                                    .delete(synchronize_session='fetch')
            db.delete(event)
            if hosting:
                db.delete(hosting)
            db.commit()
        return flask.redirect(
                   flask.url_for('display_activity',
                                 activity_id=activity_id))

    else:
        event = db.query(models.Event,
                         models.Event.id,
                         models.Event.name,
                         models.Event.description,
                         models.Event.start_date,
                         models.Event.end_date,
                         models.Event.user_id,
                         models.Event.activity_id,
                         sqlalchemy.func.to_char(
                                            models.Event.start_date,
                                            sqlalchemy.text(
                                                "'FMDay, FMMonth FMDD, FMYYYY'"
                                                )
                                            )
                         .label('starting_date'),
                         sqlalchemy.func.to_char(
                                            models.Event.start_date,
                                            sqlalchemy.text(
                                                "'FMMon FMDDth'"
                                                )
                                            )
                         .label('abbr_starting_date'),
                         sqlalchemy.func.to_char(
                                            models.Event.start_date,
                                            sqlalchemy.text(
                                                "'FMDy, FMMon FMDDth'"
                                                )
                                            )
                         .label('abbr_starting_day'),
                         sqlalchemy.func.to_char(
                                            models.Event.end_date,
                                            sqlalchemy.text(
                                                "'FMDay, FMMonth FMDD, FMYYYY'"
                                                )
                                            )
                         .label('ending_date'),
                         sqlalchemy.func.to_char(
                                            models.Event.end_date,
                                            sqlalchemy.text(
                                                "'FMMon FMDDth'"
                                                )
                                            )
                         .label('abbr_ending_date'),
                         sqlalchemy.func.to_char(
                                            models.Event.end_date,
                                            sqlalchemy.text(
                                                "'FMDy, FMMon FMDDth'"
                                                )
                                            )
                         .label('abbr_ending_day'),
                         sqlalchemy.func.to_char(
                                            models.Event._start_time,
                                            sqlalchemy.text(
                                                "'FMHH12:MI pm'"
                                                )
                                            )
                         .label('start_time'),
                         sqlalchemy.func.to_char(
                                            models.Event._end_time,
                                            sqlalchemy.text(
                                                "'FMHH12:MI pm'"
                                                )
                                            )
                         .label('end_time')
                         ) \
                  .filter_by(id=event_id,
                             activity_id=activity_id) \
                  .one()
        return flask.render_template('delete-event.html',
                                     activity=activity,
                                     event=event)


@app.route('/activities/hosting/')
@url_trace
@login_required
def display_hosting():
    """Display Event records from DB with matching user_id.

    List all Event records created by user.
    """
    with db_session() as db:
        dates = db.query(
                      models.Event,
                      sqlalchemy.func.generate_series(
                                         models.Event.start_date,
                                         models.Event.end_date,
                                         sqlalchemy.text(
                                             "'1 day'::interval"
                                             )
                                         )
                  .cast(sqlalchemy.Date)
                  .label('event_date')) \
                  .subquery()
        events = db.query(
                       models.Event,
                       models.Event.id,
                       models.Event.name,
                       models.Event.description,
                       models.Event.start_date,
                       models.Event.end_date,
                       models.Event._start_time,
                       models.Event._end_time,
                       models.Event.user_id,
                       models.Event.activity_id,
                       models.Hosting,
                       sqlalchemy.func.to_char(
                                          dates.c.event_date,
                                          sqlalchemy.text(
                                              "'FMDay, FMMonth FMDD, FMYYYY'"
                                              )
                                          )
                       .label('date'),
                       sqlalchemy.func.to_char(
                                          models.Event._start_time,
                                          sqlalchemy.text(
                                              "'FMHH12:MI pm'"
                                              )
                                          )
                       .label('start_time'),
                       sqlalchemy.func.to_char(
                                          models.Event._end_time,
                                          sqlalchemy.text(
                                              "'FMHH12:MI pm'"
                                              )
                                          )
                       .label('end_time'),
                       dates) \
                   .join(models.Hosting,
                         models.Event.id == models.Hosting.event_id) \
                   .join(dates,
                         models.Event.id == dates.c.id) \
                   .order_by(dates.c.event_date.asc(),
                             models.Event._start_time.asc(),
                             models.Event._end_time.asc()) \
                   .filter(
                       sqlalchemy.and_(
                           dates.c.event_date >= datetime.date.today(),
                           models.Hosting.user_id ==
                           get_user_id(
                                   user_email=flask.session.get('email', 0)
                                   )
                           )
                       ) \
                   .all()

    return flask.render_template('hosting.html',
                                 events=events,
                                 user_id=get_user_id(
                                             user_email=flask.session.get(
                                                 'email',
                                                 0
                                                 )
                                             ),
                                 back=flask.url_for('display_activities'))


@app.route('/activities/attending/')
@url_trace
@login_required
def display_attending():
    """Display Event records from DB that user is attending.

    List all Event records that have a corresponding entry
    in the Attending table for the user.
    """
    with db_session() as db:
        dates = db.query(
                      models.Event,
                      sqlalchemy.func.generate_series(
                                         models.Event.start_date,
                                         models.Event.end_date,
                                         sqlalchemy.text("'1 day'::interval"))
                  .cast(sqlalchemy.Date)
                  .label('event_date')) \
                  .subquery()
        events = db.query(
                       models.Event,
                       models.Event.id,
                       models.Event.name,
                       models.Event.description,
                       models.Event.start_date,
                       models.Event.end_date,
                       models.Event._start_time,
                       models.Event._end_time,
                       models.Event.user_id,
                       models.Event.activity_id,
                       models.Attending,
                       sqlalchemy.func.to_char(
                                          dates.c.event_date,
                                          sqlalchemy.text(
                                              "'FMDay, FMMonth FMDD, FMYYYY'"
                                              )
                                          )
                       .label('date'),
                       sqlalchemy.func.to_char(
                                          models.Event._start_time,
                                          sqlalchemy.text("'FMHH12:MI pm'"))
                       .label('start_time'),
                       sqlalchemy.func.to_char(
                                          models.Event._end_time,
                                          sqlalchemy.text("'FMHH12:MI pm'"))
                       .label('end_time'),
                       dates) \
                   .join(models.Attending,
                         models.Event.id == models.Attending.event_id) \
                   .join(dates,
                         models.Event.id == dates.c.id) \
                   .order_by(dates.c.event_date.asc(),
                             models.Event._start_time.asc(),
                             models.Event._end_time.asc()) \
                   .filter(
                        sqlalchemy.and_(
                            dates.c.event_date >= datetime.date.today(),
                            models.Attending.user_id == get_user_id(
                                user_email=flask.session.get('email', 0)
                                )
                            )
                        ) \
                   .all()

    return flask.render_template('attending.html',
                                 events=events,
                                 user_id=get_user_id(
                                     user_email=flask.session.get('email', 0)
                                     ),
                                 back=flask.url_for('display_activities'))


@app.route(
    '/activities/<int:activity_id>/events/<int:event_id>/attending.status/',
    methods=['GET']
    )
def check_attending_status(activity_id, event_id):
    """Check if the user is attending the associated event"""
    # User login required
    if 'username' not in flask.session:
        response = flask.make_response(
                       json.dumps('user login required'),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return response

    try:
        with db_session() as db:
            user_attending = db.query(models.Attending) \
                               .filter(
                                   sqlalchemy.and_(
                                       models.Attending.event_id == event_id,
                                       models.Attending.user_id == get_user_id(
                                           user_email=flask.session.get(
                                               'email',
                                               0
                                               )
                                           )
                                       )
                                   ) \
                               .first()
    except (sqlalchemy.exc.DBAPIError, sqlalchemy.exc.SQLAlchemyError) as err:
        response = flask.make_response(
                       json.dumps('database error encountered'),
                       500)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        if user_attending:
            response = json.dumps(
                {'Attending_Status_Image': flask.url_for(
                                               'static',
                                               filename='img/attending.svg'
                                               ),
                 'Attending_Status_Button': 'leaveEvent()'}
            )
        else:
            response = json.dumps(
                {'Attending_Status_Image': flask.url_for(
                                               'static',
                                               filename='img/not-attending.svg'
                                               ),
                 'Attending_Status_Button': 'attendEvent()'}
            )

        return response


@app.route(
    '/activities/<int:activity_id>/events/<int:event_id>/attend/',
    methods=['POST']
    )
def attend_event(activity_id, event_id):
    """Update attending table to show user is attending the associated event"""
    # User login required
    if 'username' not in flask.session:
        response = flask.make_response(
                       json.dumps('user login required'),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return response

    try:
        with db_session() as db:
            user_attending = db.query(models.Attending) \
                               .filter(
                                   sqlalchemy.and_(
                                       models.Attending.event_id == event_id,
                                       models.Attending.user_id == get_user_id(
                                           user_email=flask.session.get(
                                               'email',
                                               0
                                               )
                                           )
                                       )
                                   ) \
                               .first()
            user_considering = db.query(models.Considering) \
                                 .filter(
                                   sqlalchemy.and_(
                                     models.Considering.event_id == event_id,
                                     models.Considering.user_id == get_user_id(
                                         user_email=flask.session.get(
                                             'email',
                                             0
                                             )
                                         )
                                     )
                                  ) \
                                 .first()
    except (sqlalchemy.exc.DBAPIError, sqlalchemy.exc.SQLAlchemyError) as err:
        response = flask.make_response(
                       json.dumps('database error encountered'),
                       500)
        response.headers['Content-Type'] = 'application/json'
        return response

    if user_attending:
        response = flask.make_response(
                       json.dumps('user already attending'),
                       500)
        response.headers['Content-Type'] = 'application/json'
        return response

    try:
        with db_session() as db:
            attend_event = models.Attending(event_id=event_id,
                                            user_id=get_user_id(
                                                user_email=flask.session[
                                                               'email'
                                                               ]
                                                )
                                            )
            if user_considering:
                db.delete(user_considering)
            db.add(attend_event)
            db.commit()
    except (sqlalchemy.exc.DBAPIError, sqlalchemy.exc.SQLAlchemyError) as err:
        response = flask.make_response(
                       json.dumps('database error encountered'),
                       500)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = flask.make_response(
                     json.dumps('successfully marked as attending event'),
                     200)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route(
    '/activities/<int:activity_id>/events/<int:event_id>/leave/',
    methods=['POST']
    )
def leave_event(activity_id, event_id):
    """Update attending table to show user is not attending associated event"""
    # User login required
    if 'username' not in flask.session:
        response = flask.make_response(
                       json.dumps('user login required'),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return response

    try:
        with db_session() as db:
            user_attending = db.query(models.Attending) \
                               .filter(
                                   sqlalchemy.and_(
                                       models.Attending.event_id == event_id,
                                       models.Attending.user_id ==
                                       get_user_id(
                                           user_email=flask.session.get(
                                               'email',
                                               0
                                               )
                                           )
                                       )
                                   ) \
                               .first()
    except (sqlalchemy.exc.DBAPIError, sqlalchemy.exc.SQLAlchemyError) as err:
        response = flask.make_response(
                       json.dumps('database error encountered'),
                       500)
        response.headers['Content-Type'] = 'application/json'
        return response

    if not user_attending:
        response = flask.make_response(
                       json.dumps('user was not attending event'),
                       500)
        response.headers['Content-Type'] = 'application/json'
        return response

    try:
        with db_session() as db:
            db.delete(user_attending)
            db.commit()
    except (sqlalchemy.exc.DBAPIError, sqlalchemy.exc.SQLAlchemyError) as err:
        response = flask.make_response(
                       json.dumps('database error encountered'),
                       500)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = flask.make_response(
                     json.dumps('successfully marked as not attending event'),
                     200)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route(
    '/activities/<int:activity_id>/events/<int:event_id>/considering.status/',
    methods=['GET']
    )
def check_considering_status(activity_id, event_id):
    """Check if the user is considering attending the associated event"""
    # User login required
    if 'username' not in flask.session:
        response = flask.make_response(
                       json.dumps('user login required'),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return response

    try:
        with db_session() as db:
            user_considering = db.query(models.Considering) \
                                 .filter(
                                   sqlalchemy.and_(
                                     models.Considering.event_id == event_id,
                                     models.Considering.user_id == get_user_id(
                                           user_email=flask.session.get(
                                               'email',
                                               0
                                               )
                                           )
                                       )
                                   ) \
                               .first()
    except (sqlalchemy.exc.DBAPIError, sqlalchemy.exc.SQLAlchemyError) as err:
        response = flask.make_response(
                       json.dumps('database error encountered'),
                       500)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        if user_considering:
            response = json.dumps(
                {'Considering_Status_Image': flask.url_for(
                                               'static',
                                               filename='img/considering.svg'
                                               ),
                 'Considering_Status_Button': 'unconsiderEvent()'}
            )
        else:
            response = json.dumps(
                {'Considering_Status_Image':
                    flask.url_for('static',
                                  filename='img/not-considering.svg'
                                  ),
                 'Considering_Status_Button': 'considerEvent()'}
            )

        return response


@app.route('/activities/considering/')
@url_trace
@login_required
def display_considering():
    """Display Event records from DB that user is considering.

    List all Event records that have a corresponding entry
    in the Considering table for the user.
    """
    with db_session() as db:
        dates = db.query(
                      models.Event,
                      sqlalchemy.func.generate_series(
                                         models.Event.start_date,
                                         models.Event.end_date,
                                         sqlalchemy.text("'1 day'::interval"))
                  .cast(sqlalchemy.Date)
                  .label('event_date')) \
                  .subquery()
        events = db.query(
                       models.Event,
                       models.Event.id,
                       models.Event.name,
                       models.Event.description,
                       models.Event.start_date,
                       models.Event.end_date,
                       models.Event._start_time,
                       models.Event._end_time,
                       models.Event.user_id,
                       models.Event.activity_id,
                       models.Considering,
                       sqlalchemy.func.to_char(
                                          dates.c.event_date,
                                          sqlalchemy.text(
                                              "'FMDay, FMMonth FMDD, FMYYYY'"
                                              )
                                          )
                       .label('date'),
                       sqlalchemy.func.to_char(
                                          models.Event._start_time,
                                          sqlalchemy.text("'FMHH12:MI pm'"))
                       .label('start_time'),
                       sqlalchemy.func.to_char(
                                          models.Event._end_time,
                                          sqlalchemy.text("'FMHH12:MI pm'"))
                       .label('end_time'),
                       dates) \
                   .join(models.Considering,
                         models.Event.id == models.Considering.event_id) \
                   .join(dates,
                         models.Event.id == dates.c.id) \
                   .order_by(dates.c.event_date.asc(),
                             models.Event._start_time.asc(),
                             models.Event._end_time.asc()) \
                   .filter(
                        sqlalchemy.and_(
                            dates.c.event_date >= datetime.date.today(),
                            models.Considering.user_id == get_user_id(
                                user_email=flask.session.get('email', 0)
                                )
                            )
                        ) \
                   .all()

    return flask.render_template('considering.html',
                                 events=events,
                                 user_id=get_user_id(
                                     user_email=flask.session.get('email', 0)
                                     ),
                                 back=flask.url_for('display_activities'))


@app.route(
    '/activities/<int:activity_id>/events/<int:event_id>/consider/',
    methods=['POST']
    )
def consider_event(activity_id, event_id):
    """Update attending table to show user is considering the event"""
    # User login required
    if 'username' not in flask.session:
        response = flask.make_response(
                       json.dumps('user login required'),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return response

    try:
        with db_session() as db:
            user_attending = db.query(models.Attending) \
                               .filter(
                                   sqlalchemy.and_(
                                       models.Attending.event_id == event_id,
                                       models.Attending.user_id == get_user_id(
                                           user_email=flask.session.get(
                                               'email',
                                               0
                                               )
                                           )
                                       )
                                   ) \
                               .first()
            user_considering = db.query(models.Considering) \
                                 .filter(
                                   sqlalchemy.and_(
                                     models.Considering.event_id == event_id,
                                     models.Considering.user_id == get_user_id(
                                         user_email=flask.session.get(
                                             'email',
                                             0
                                             )
                                         )
                                     )
                                  ) \
                                 .first()
    except (sqlalchemy.exc.DBAPIError, sqlalchemy.exc.SQLAlchemyError) as err:
        response = flask.make_response(
                       json.dumps('database error encountered'),
                       500)
        response.headers['Content-Type'] = 'application/json'
        return response

    if user_considering:
        response = flask.make_response(
                       json.dumps('user already considering'),
                       500)
        response.headers['Content-Type'] = 'application/json'
        return response

    try:
        with db_session() as db:
            consider_event = models.Considering(event_id=event_id,
                                                user_id=get_user_id(
                                                    user_email=flask.session[
                                                                   'email'
                                                                   ]
                                                    )
                                                )
            if user_attending:
                db.delete(user_attending)
            db.add(consider_event)
            db.commit()
    except (sqlalchemy.exc.DBAPIError, sqlalchemy.exc.SQLAlchemyError) as err:
        response = flask.make_response(
                       json.dumps('database error encountered'),
                       500)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = flask.make_response(
                     json.dumps('successfully marked as considering event'),
                     200)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route(
    '/activities/<int:activity_id>/events/<int:event_id>/unconsider/',
    methods=['POST']
    )
def unconsider_event(activity_id, event_id):
    """Update considering table to show user has unconsidered the event"""
    # User login required
    if 'username' not in flask.session:
        response = flask.make_response(
                       json.dumps('user login required'),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return response

    try:
        with db_session() as db:
            user_considering = db.query(models.Considering) \
                                 .filter(
                                   sqlalchemy.and_(
                                     models.Considering.event_id == event_id,
                                     models.Considering.user_id == get_user_id(
                                         user_email=flask.session.get(
                                             'email',
                                             0
                                             )
                                         )
                                     )
                                 ) \
                               .first()
    except (sqlalchemy.exc.DBAPIError, sqlalchemy.exc.SQLAlchemyError) as err:
        response = flask.make_response(
                       json.dumps('database error encountered'),
                       500)
        response.headers['Content-Type'] = 'application/json'
        return response

    if not user_considering:
        response = flask.make_response(
                       json.dumps('user was not considering event'),
                       500)
        response.headers['Content-Type'] = 'application/json'
        return response

    try:
        with db_session() as db:
            db.delete(user_considering)
            db.commit()
    except (sqlalchemy.exc.DBAPIError, sqlalchemy.exc.SQLAlchemyError) as err:
        response = flask.make_response(
                       json.dumps('database error encountered'),
                       500)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = flask.make_response(
                     json.dumps(
                         'successfully marked as not considering event'
                     ),
                     200)
        response.headers['Content-Type'] = 'application/json'
        return response


def hosting_events():
    """Return a list of ids for all events being hosted by the user"""
    # User login required
    if 'username' not in flask.session:
        response = flask.make_response(
                       json.dumps('user login required'),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return response

    try:
        with db_session() as db:
            hosted_events = db.query(models.Hosting) \
                              .order_by(models.Hosting.event_id.asc()) \
                              .filter(sqlalchemy.and_(
                                models.Hosting.user_id ==
                                get_user_id(
                                  user_email=flask.session.get('email', 0)
                                  )
                                )
                              ) \
                              .all()
    except (sqlalchemy.exc.DBAPIError, sqlalchemy.exc.SQLAlchemyError) as err:
        response = flask.make_response(
                       json.dumps('database error encountered'),
                       500)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        hosted_event_ids = [event.event_id for event in hosted_events]
        return hosted_event_ids


def attending_events():
    """Return a list of ids for all events being attended by the user"""
    # User login required
    if 'username' not in flask.session:
        response = flask.make_response(
                       json.dumps('user login required'),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return response

    try:
        with db_session() as db:
            attended_events = db.query(models.Attending) \
                                .order_by(models.Attending.event_id.asc()) \
                                .filter(sqlalchemy.and_(
                                  models.Attending.user_id ==
                                  get_user_id(
                                    user_email=flask.session.get('email', 0)
                                    )
                                  )
                                ) \
                                .all()
    except (sqlalchemy.exc.DBAPIError, sqlalchemy.exc.SQLAlchemyError) as err:
        response = flask.make_response(
                       json.dumps('database error encountered'),
                       500)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        attended_event_ids = [event.event_id for event in attended_events]
        return attended_event_ids


def considering_events():
    """Return a list of ids for all events being considered by the user"""
    # User login required
    if 'username' not in flask.session:
        response = flask.make_response(
                       json.dumps('user login required'),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return response

    try:
        with db_session() as db:
            considered_events = db.query(models.Considering) \
                                .order_by(models.Considering.event_id.asc()) \
                                .filter(sqlalchemy.and_(
                                  models.Considering.user_id ==
                                  get_user_id(
                                    user_email=flask.session.get('email', 0)
                                    )
                                  )
                                ) \
                                .all()
    except (sqlalchemy.exc.DBAPIError, sqlalchemy.exc.SQLAlchemyError) as err:
        response = flask.make_response(
                       json.dumps('database error encountered'),
                       500)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        considered_event_ids = [event.event_id for event in considered_events]
        return considered_event_ids


def make_user(*, session):
    """Create User object.

    Create a new user account and insert into DB. Return its id field.

    Args:
        session: flask session.

    Returns:
        The id field of the created user account record.

    Dependencies:
        models.UserAccount
        flask.session
        sqlalchemy
    """
    try:
        new_user = models.UserAccount(name=session['username'],
                                      email=session['email'],
                                      picture=session['picture'])
        with db_session() as db:
            db.add(new_user)
            db.commit()
            user = db.query(models.UserAccount) \
                     .filter_by(email=session['email']) \
                     .one()
    except (sqlalchemy.exc.DBAPIError, sqlalchemy.exc.SQLAlchemyError) as err:
        # database error
        pass
    else:
        return user.id


def get_user(*, user_id):
    """Returns user account object corresponding to the id passed to function.

    Args:
        user_id = id field corresponding to user record.

    Returns:
        User account record matching the user_id.

    Dependencies:
        models.UserAccount
        sqlalchemy
    """
    try:
        with db_session() as db:
            user = db.query(models.UserAccount) \
                     .filter_by(id=user_id) \
                     .one()
    except (sqlalchemy.exc.DBAPIError, sqlalchemy.exc.SQLAlchemyError) as err:
        # database error
        pass
    else:
        return user


def get_user_id(*, user_email):
    """If email matches a user record, returns its id field. Else, None.

    Args:
        user_email = email used to search for corresponding user record.

    Returns:
        id field from user account record matching user_email. Else, None.

    Dependencies:
        models.UserAccount
        sqlalchemy
    """
    try:
        with db_session() as db:
            user = db.query(models.UserAccount) \
                     .filter_by(email=user_email) \
                     .one()
    except (sqlalchemy.exc.DBAPIError, sqlalchemy.exc.SQLAlchemyError) as err:
        return None
    else:
        return user.id


@app.route('/activities/JSON/')
def activities_endpoint():
    """Returns a JSON endpoint for all activities"""
    activities = []
    try:
        with db_session() as db:
            for activity in db.query(models.Activity).all():
                activity = activity.serialize
                activity['events'] = [event.serialize for event in
                                      db.query(models.Event)
                                        .filter_by(activity_id=activity['id'])
                                        .all()]
                activities.append(activity)
    except (sqlalchemy.exc.DBAPIError, sqlalchemy.exc.SQLAlchemyError) as err:
        return flask.jsonify({
                              'status': 500,
                              'error': 'database error',
                             })
    else:
        if not activities:
            return flask.jsonify({
                                  'status': 404,
                                  'error': 'activities not found',
                                 })
        else:
            return flask.jsonify(activities)


@app.route('/activities/<int:activity_id>/events/JSON/')
def activity_endpoint(activity_id):
    """Returns a JSON endpoint for an activity"""
    try:
        with db_session() as db:
            activity = db.query(models.Activity) \
                         .filter_by(id=activity_id) \
                         .one()
    except (sqlalchemy.exc.DBAPIError, sqlalchemy.exc.SQLAlchemyError) as err:
        return flask.jsonify({
                              'status': 404,
                              'error': 'activity not found',
                             })
    else:
        activity = activity.serialize
        with db_session() as db:
            activity['events'] = [event.serialize for event in
                                  db.query(models.Event)
                                    .filter_by(activity_id=activity_id)
                                    .all()]
        return flask.jsonify(activity)


@app.route('/activities/<int:activity_id>/events/<int:event_id>/JSON/')
def event_endpoint(activity_id, event_id):
    """Returns a JSON endpoint for an event"""
    try:
        with db_session() as db:
            event = db.query(models.Event) \
                      .filter_by(id=event_id) \
                      .one()
    except (sqlalchemy.exc.DBAPIError, sqlalchemy.exc.SQLAlchemyError) as err:
        return flask.jsonify({
                              'status': 404,
                              'error': 'event not found',
                             })
    else:
        return flask.jsonify(event.serialize)


if __name__ == '__main__':
    """Runs app on a local development server"""

    app.debug = True
    app.secret_key = 'PLACEHOLDER FOR DEV TESTING'
    app.run(host='0.0.0.0', port=5000)
