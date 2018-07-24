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
import models
import oauth2client.client
import os
import random
import re
import requests
import sqlalchemy
import string


CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']

logging.config.dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '{asctime} - {levelname:8} in {module:9}: {message}',
        'style': '{',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})

app = flask.Flask(__name__)

engine = sqlalchemy.create_engine(models.DB)
models.declarative_base.metadata.bind = engine
create_sqlalchemy_session = sqlalchemy.orm.sessionmaker(bind=engine)

@contextlib.contextmanager
def db_session():
    db = create_sqlalchemy_session()
    try:
        yield db
    except:
        db.rollback()
        raise
    finally:
        db.close()


def entry_and_exit_logger(func):
    """Performs DEBUG level logging when entering and exiting function.

    Logs function name and arguments when entering the function.
    Logs function name and any return values when exiting the function.

    Args:
        func: Function to be decorated by entry_and_exit_logger.

    Returns:
        entry_and_exit_wrapper: Wrapper that extends the behavior of func
            to include entry and exit logging.

    Dependencies:
        functools.wraps
    """
    @functools.wraps(func)
    def entry_and_exit_wrapper(*args, **kwargs):
        """Entry and exit log wrapper."""
        try:
            input_args = ', '.join(str(arg) for arg in args)
        except:
            input_args = ''

        try:
            input_kwargs = ', '.join('{}={}'.format(k, v)
                                     for k, v in kwargs.items())
        except:
            input_kwargs = ''

        if input_args and input_kwargs:
            arguments = '{}, {}'.format(input_args, input_kwargs)
        elif input_args:
            arguments = input_args
        elif input_kwargs:
            arguments = input_kwargs
        else:
            arguments = ''

        message = '{action:6} {arguments}'
        func_params = {'arguments': '{}({})'.format(func.__name__, arguments),
                       'action': 'ENTER'}
        app.logger.debug(message.format(**func_params))

        result = func(*args, **kwargs)

        func_params['arguments'] = '{}({}={})'.format(func.__name__,
                                                      'result', result)
        func_params['action'] = 'EXIT'
        app.logger.debug(message.format(**func_params))
        return result
    return entry_and_exit_wrapper


@entry_and_exit_logger
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


@entry_and_exit_logger
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
    patterns = ['(?P<year>[\d]{4})[-/]?'
                '(?P<month>[\d]{1,2})[-/]?'
                '(?P<day>[\d]{1,2})',
                '(?P<month>[\d]{1,2})[-/]?'
                '(?P<day>[\d]{1,2})[-/]?'
                '(?P<year>[\d]{4})',
                '(?P<month>' + _MONTHS + '){1}\s'
                '(?P<day>[\d]{1,2})\,?\s(?P<year>[\d]{4})']

    for pattern in patterns:
        if re.match(pattern, str_input, re.IGNORECASE):
            return re.match(pattern, str_input, re.IGNORECASE).groupdict()


@entry_and_exit_logger
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
    patterns = ['(?P<hours>[\d]{1,2})[:]{1}'
                '(?P<minutes>[\d]{2})[:]{1}'
                '(?P<seconds>[\d]{2})'
                '(?P<timezone>[+-]?[\d]{2}[:]{1}[\d]{2})',
                '(?P<hours>[\d]{1,2})[:]{1}'
                '(?P<minutes>[\d]{2})[:]{1}'
                '(?P<seconds>[\d]{2})\s?'
                '(?P<twelve_hr>am|pm|a\.m\.|p\.m\.){1}',
                '(?P<hours>[\d]{1,2})[:]{1}'
                '(?P<minutes>[\d]{2})\s?'
                '(?P<twelve_hr>am|pm|a\.m\.|p\.m\.){1}',
                '(?P<hours>[\d]{1,2})[:]{1}'
                '(?P<minutes>[\d]{2})[:]{1}'
                '(?P<seconds>[\d]{2})',
                '(?P<hours>[\d]{1,2})[:]{1}'
                '(?P<minutes>[\d]{2})']
    for pattern in patterns:
        if re.match(pattern, str_input, re.IGNORECASE):
            return re.match(pattern, str_input, re.IGNORECASE).groupdict()


@entry_and_exit_logger
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
    except:
        pass

    try:
        event_date = datetime.date(int(date_dict['year']),
                                   int(date_dict['month']),
                                   int(date_dict['day']))
    except (TypeError, ValueError) as err:
        return None
    else:
        return event_date


@entry_and_exit_logger
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
    except:
        pass

    try:
        if time_dict['twelve_hr'].lower()[0] is 'p':
            time_dict['hours'] = time_dict['hours'] + 12
    except:
        pass

    try:
        event_time = datetime.time(hour=time_dict['hours'],
                                   minute=time_dict['minutes'])
    except (TypeError, ValueError) as err:
        return None
    else:
        return event_time


@entry_and_exit_logger
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


@entry_and_exit_logger
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


@entry_and_exit_logger
def set_event_fields(event):
    """Set or update Event object fields.

    Use in a POST method to return an updated Event object. Event
    fields will be updated from str values pulled from form data.

    Args:
        event: Event object.

    Returns:
        event: Updated Event object.

    Dependencies:
        models.Event
        date_checker()
        time_checker()
    """
    if flask.request.form['name']:
        event.name = flask.request.form['name']

    if flask.request.form['description']:
        event.description = flask.request.form['description']
    else:
        event.description = 'please add a description'

    # determine start/end dates based on available input.
    start_date, end_date = None, None

    if flask.request.form['start_date']:
        start_date = flask.request.form['start_date']
        start_date = date_checker(start_date)

    if flask.request.form['end_date']:
        end_date = flask.request.form['end_date']
        end_date = date_checker(end_date)

    if start_date and end_date:
        event.start_date, event.end_date = start_date, end_date
    elif start_date:
        event.start_date, event.end_date = start_date, start_date
    elif end_date:
        event.start_date, event.end_date = end_date, end_date

    # determine start/end times based on available input.
    if flask.request.form['start_time']:
        start_time = flask.request.form['start_time']
        start_time = time_checker(start_time)
        if start_time:
            event.start_time = start_time
    if flask.request.form['end_time']:
        end_time = flask.request.form['end_time']
        end_time = time_checker(end_time)
        if end_time:
            event.end_time = end_time
    return event


@app.route('/')
@app.route('/activities/')
@entry_and_exit_logger
def display_activities():
    """Display all Activity records from DB."""
    with db_session() as db:
        activities = db.query(models.Activity)
    return flask.render_template('activities.html',
                                 activities=activities)


@app.route('/login/')
@entry_and_exit_logger
def user_login():
    """Create an anti-forgery state token and store it in the session"""
    state = hashlib.sha256(os.urandom(1024)).hexdigest()
    flask.session['state'] = state

    if 'prelogin_page' not in flask.session:
        flask.session['prelogin_page'] = '/'

    google_oauth_2_0 = (
        "//ajax.googleapis.com/ajax/libs/jquery/1.8.2/jquery.min.js",
        "//apis.google.com/js/platform.js?onload=start")

    return flask.render_template('login.html',
                                 STATE=state,
                                 redirect_to=flask.session['prelogin_page'],
                                 load_scripts=(google_oauth_2_0))


@app.route('/logout/')
@entry_and_exit_logger
def user_logout():
    """Logout user"""
    try:
        oauth_provider = flask.session['oauth_provider']
        app.logger.info(
            ('user_logout() - - VARS'
             '     [Oauth Provider: {}]'.format(oauth_provider)))
    except:
        app.logger.info(
            ('user_logout() - - MSG'
             '     [Error: Oauth provider not detected.]'))
        response = flask.make_response(
                     json.dumps('Current user not logged in.'),
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
                       json.dumps('Invalid state parameter'),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return (False, response)
    else:
        return (True, None)


def login_splash_page(*, picture):
    """display login splash page"""
    return ('<img src="{}" id="login-image">'.format(flask.session['picture']))


@app.route('/google.connect/', methods=['POST'])
@entry_and_exit_logger
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
                         'client_secret.json',
                         scope=['email', 'openid'],
                         redirect_uri='postmessage')
        # Exchange authorization code for a Credentials object
        credentials = oauth_flow.step2_exchange(code)
    except oauth2client.client.InvalidClientSecretsError:
        # Format of ClientSecrets file is invalid.
        response = flask.make_response(
                       json.dumps(('Format of ClientSecrets'
                                   ' file is invalid.')),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return response
    except oauth2client.client.FlowExchangeError:
        # Error trying to exchange an authorization grant for an access token.
        response = flask.make_response(
                       json.dumps(('Error trying to exchange'
                                   ' an authorization grant'
                                   ' for an access token.')),
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
                       json.dumps(("Token's user ID does not"
                                   " match given user ID.")),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = flask.make_response(
                       json.dumps("Token's client ID does not match app's."),
                       401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = flask.session.get('access_token')
    stored_google_account_id = flask.session.get('google_account_id')
    if (stored_access_token is not None and
            google_account_id == stored_google_account_id):
        response = flask.make_response(
                       json.dumps('Current user is already connected.'),
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

    return login_splash_page(picture=flask.session['picture']) + flask.session['username']


@app.route('/google.disconnect/')
@entry_and_exit_logger
def google_disconnect():
    """Disconnect a login session that was setup with Google"""
    access_token = flask.session.get('access_token')
    if access_token is None:
        app.logger.info(
            ('google_disconnect() - - MSG'
             '     [Access Token is None]'))
        response = flask.make_response(
                     json.dumps('Current user not connected.'),
                     401)
        response.headers['Content-Type'] = 'application/json'
        return response

    app.logger.info(
        ('google_disconnect() - - VARS'
         '    [Access Token: {}]'.format(access_token)))
    app.logger.info(
        ('google_disconnect() - - VARS'
         '    [User Name: {}]'.format(flask.session['username'])))
    url = ('https://accounts.google.com/o/oauth2/revoke?'
           'token={}'.format(flask.session['access_token']))
    http = httplib2.Http()
    result = http.request(url, 'GET')[0]
    app.logger.info(
        ('google_disconnect() - - VARS'
         '    [Result: {}]'.format(result)))

    if result['status'] == '200':
        del flask.session['oauth_provider']
        del flask.session['access_token']
        del flask.session['google_account_id']
        del flask.session['username']
        del flask.session['email']
        del flask.session['picture']
        del flask.session['prelogin_page']

        response = flask.make_response(
                       json.dumps('Successfully disconnected.'),
                       200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = flask.make_response(
                       json.dumps('Failed to revoke token for given user.'),
                       400)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/facebook.connect/', methods=['POST'])
@entry_and_exit_logger
def facebook_connect():
    """OAuth via Facebook"""
    validated, response = validate_state_token()
    if not validated:
        return response

    # Obtain short-lived access token and decode from bytes
    access_token = str(flask.request.data, 'utf-8')
    app.logger.info(
        ('facebook_connect() - - VARS'
         '    [Short-Lived Access Token: {}]'.format(access_token)))

    # Construct url to request long-lived token from Facebook
    fb_client_secret = json.loads(open('fb_client_secret.json', 'r').read())
    app_id = fb_client_secret['web']['app_id']
    app_secret = fb_client_secret['web']['app_secret']
    url = ('https://graph.facebook.com/oauth/access_token?'
           'grant_type=fb_exchange_token&client_id={}&client_secret={}&'
           'fb_exchange_token={}'.format(app_id, app_secret, access_token))
    app.logger.info(
        ('facebook_connect() - - VARS'
         '    [url: {}]'.format(url)))

    try:
        # Request long-lived token from Facebook.
        http = httplib2.Http()
        http_response, http_content = http.request(url, 'GET')
        app.logger.info(
            ('facebook_connect() - - VARS'
             '    [http.request.response: {}]'.format(http_response)))
        app.logger.info(
            ('facebook_connect() - - VARS'
             '    [http.request.content: {}]'.format(http_content)))

        # Convert from bytes to str to Python object.
        result = json.loads(str(http_content, 'utf-8'))
        app.logger.info(
            ('facebook_connect() - - VARS'
             '    [result: {}]'.format(result)))
    except json.decoder.JSONDecodeError:
        app.logger.error(
            ('facebook_connect() - - VARS'
             '    [JSONDecodeError: {}]'.format(("Exception when converting"
                                                 " http_content to Python"
                                                 " object."))))
        response = flask.make_response(
                       json.dumps(('Format of ``str`` instance containing'
                                   ' a JSON document is invalid.')),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return response
    except httplib2.RelativeURIError:
        app.logger.error(
            ('facebook_connect() - - VARS'
             '    [RelativeURIError: {}]'.format(("Format of Facebook exchange"
                                                  " token URL is invalid."))))
        response = flask.make_response(
            json.dumps('Format of Facebook exchange token URL is invalid.'),
            401)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        app.logger.info('facebook_connect() - - VARS'
                        '    [Facebook Reply: {}]'.format(result))
        if result.get('access_token'):
            token = result['access_token']
            app.logger.info('facebook_connect() - - VARS'
                            '    [Token: {}]'.format(token))
        else:
            # Error exchanging short-lived token for a long-lived token.
            response = flask.make_response(
                           json.dumps(('Error trying to exchange a'
                                       ' short-lived access token for'
                                       ' a long-lived access token.')),
                           500)
            response.headers['Content-Type'] = 'application/json'
            return response

    app.logger.info(
        ('facebook_connect() - - VARS'
         '    [Long-Lived Token: {}]'.format(token)))

    # Get user info
    url = ('https://graph.facebook.com/v2.11/me?'
           'access_token={}&fields=name,id,email'.format(token))
    http = httplib2.Http()
    result = str(http.request(url, 'GET')[1], 'utf-8')
    app.logger.info(
        ('facebook_connect() - - VARS'
         '    [Facebook API Call: {}]'.format(result)))

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
    app.logger.info(
        ('facebook_connect() - - VARS'
         '    [Facebook Picture: {}]'.format(result)))
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
@entry_and_exit_logger
def facebook_disconnect():
    """Disconnect a login session that was setup with Facebook"""
    facebook_id = flask.session.get('facebook_id')
    if facebook_id is None:
        app.logger.info(
            ('facebook_disconnect() - - MSG'
             '    [Facebook ID is None]'))
        response = flask.make_response(
                       json.dumps('Current user not connected.'),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return response

    app.logger.info(
        ('facebook_disconnect() - - VARS'
         '    [Facebook ID: {}]'.format(facebook_id)))
    app.logger.info(
        ('facebook_disconnect() - - VARS'
         '    [User Name: {}]'.format(flask.session['username'])))

    url = ('https://graph.facebook.com/{}/permissions?'
           'access_token={}'.format(facebook_id,
                                    flask.session['access_token']))
    http = httplib2.Http()
    result = json.loads(str(http.request(url, 'DELETE')[1], 'utf-8'))

    app.logger.info(
        ('facebook_disconnect() - - VARS'
         '    [Result: {}]'.format(result)))

    logged_out = result.get('success')
    if logged_out:
        del flask.session['oauth_provider']
        del flask.session['access_token']
        del flask.session['facebook_id']
        del flask.session['username']
        del flask.session['email']
        del flask.session['picture']
        del flask.session['prelogin_page']

        response = flask.make_response(
                     json.dumps('Successfully disconnected.'),
                     200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = flask.make_response(
                     json.dumps('Failed to revoke token for given user.'),
                     400)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/activities/<int:activity_id>/')
@app.route('/activities/<int:activity_id>/events/')
@entry_and_exit_logger
def display_activity(activity_id):
    """Display Activity record from DB with matching activity_id.

    Display Activity and list all Event records corresponding to it.

    Activity query as SQL:

        query = "SELECT * FROM " \
                    "(SELECT *, " \
                          "to_char(event_date, 'day') AS day_of_week, " \
                          "to_char(event_date, 'month') AS month, " \
                          "extract(day from event_date)::int AS day_of_month, " \
                          "extract(year from event_date)::int AS year, " \
                          "to_char(_start_time, 'HH12:MI AM') AS start_time, " \
                          "to_char(_end_time, 'HH12:MI AM') AS end_time " \
                          " FROM (SELECT *, generate_series(event.start_date," \
                                                           "event.end_date, " \
                                                           "'1 day'::interval)::date "\
                                "AS event_date " \
                                "FROM event " \
                                "WHERE activity_id = {} " \
                                "GROUP BY id) "\
                          "AS sq1) "\
                    "AS sq2 "\
                "WHERE event_date >= current_date " \
                "ORDER BY event_date " \
                "ASC;".format(activity.id)
        events = db.execute(sqlalchemy.text(query))
"""
    with db_session() as db:
        activity = db.query(models.Activity) \
                     .filter_by(id=activity_id) \
                     .one()
        dates = db.query(models.Event,
                         sqlalchemy.func.generate_series(models.Event.start_date,
                                                         models.Event.end_date,
                                                         sqlalchemy.text("'1 day'::interval")) \
                  .label('event_date')) \
                  .subquery()
        events = db.query(models.Event,
                          models.Event.id,
                          models.Event.name,
                          models.Event.description,
                          models.Event.start_date,
                          models.Event.end_date,
                          models.Event._start_time,
                          models.Event._end_time,
                          models.Event.user_id,
                          models.Event.activity_id,
                          sqlalchemy.func.to_char(dates.c.event_date,
                                                  sqlalchemy.text("'FMDay'")) \
                                         .label('day_of_week'), \
                          sqlalchemy.func.to_char(dates.c.event_date,
                                                  sqlalchemy.text("'FMMonth'")) \
                                         .label('month'), \
                          sqlalchemy.func.extract(sqlalchemy.text("'day'"),
                                                  dates.c.event_date) \
                                         .cast(sqlalchemy.Integer) \
                                         .label('day_of_month'), \
                          sqlalchemy.func.extract(sqlalchemy.text("'year'"),
                                                  dates.c.event_date) \
                                         .cast(sqlalchemy.Integer) \
                                         .label('year'), \
                          sqlalchemy.func.to_char(models.Event._start_time,
                                                  sqlalchemy.text("'FMHH12:MI pm'")) \
                                         .label('start_time'), \
                          sqlalchemy.func.to_char(models.Event._end_time,
                                                  sqlalchemy.text("'FMHH12:MI pm'")) \
                                         .label('end_time'), \
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
                                 user_id=get_user_id(user_email=flask.session.get('email', 0)),
                                 back= flask.url_for('display_activities'))


@app.route('/activities/new/', methods=['GET', 'POST'])
@entry_and_exit_logger
def make_activity():
    """Create new Activity record in DB"""
    # User login required
    if 'username' not in flask.session:
        # Store current page to redirect back to after login
        flask.session['prelogin_page'] = flask.url_for('make_activity')
        return flask.redirect('/login/')

    if flask.request.method == 'POST':
        new_activity = models.Activity(
                           name=flask.request.form['name'],
                           icon=flask.request.form['icon'],
                           user_id=get_user_id(
                                       user_email=flask.session['email']))
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
@entry_and_exit_logger
def update_activity(activity_id):
    """Update Activity record in DB with matching activity_id"""
    # User login required
    if 'username' not in flask.session:
        # Store current page to redirect back to after login
        flask.session['prelogin_page'] = flask.url_for(
                                             'update_activity',
                                             activity_id=activity_id)
        return flask.redirect('/login/')
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
        if flask.request.form['name']:
            activity.name = flask.request.form['name']
        if flask.request.form['icon']:
            activity.icon = flask.request.form['icon']
        with db_session() as db:
            db.add(activity)
            db.commit()

            return flask.redirect(
                       flask.url_for('display_activity',
                                     activity_id=activity.id))
    else:
        icons = models.icon_list()
        return flask.render_template('edit-activity.html',
                                     activity=activity,
                                     icons=icons)


@app.route('/activities/<int:activity_id>/delete/', methods=['GET', 'POST'])
@entry_and_exit_logger
def delete_activity(activity_id):
    """Delete Activity record in DB with matching activity_id"""
    # User login required
    if 'username' not in flask.session:
        # Store current page to redirect back to after login
        flask.session['prelogin_page'] = flask.url_for(
                                             'delete_activity',
                                             activity_id=activity_id)
        return flask.redirect('/login/')
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
@entry_and_exit_logger
def display_event(activity_id, event_id):
    """Display Event record from DB with matching event_id"""
    with db_session() as db:
        activity = db.query(models.Activity) \
                     .filter_by(id=activity_id) \
                     .one()
        event = db.query(models.Event) \
                  .filter_by(id=event_id,
                             activity_id=activity_id) \
                  .one()
    return flask.render_template('event.html',
                                 activity=activity,
                                 event=event,
                                 user_id=get_user_id(user_email=flask.session.get('email', 0)),
                                 back= flask.url_for('display_activity',
                                                     activity_id=activity.id))


@app.route('/activities/<int:activity_id>/events/new/',
           methods=['GET', 'POST'])
@entry_and_exit_logger
def make_event(activity_id):
    """Create new Event record in DB"""
    # User login required
    if 'username' not in flask.session:
        # Store current page to redirect back to after login
        flask.session['prelogin_page'] = flask.url_for(
                                             'make_event',
                                             activity_id=activity_id)
        return flask.redirect('/login/')

    if flask.request.method == 'POST':
        new_event = models.Event(name=flask.request.form['name'],
                                 activity_id=activity_id,
                                 user_id=get_user_id(
                                             user_email=flask.session['email']
                                         )
                                 )
        new_event = set_event_fields(new_event)
        with db_session() as db:
            db.add(new_event)
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
@entry_and_exit_logger
def update_event(activity_id, event_id):
    """Update Event record in DB with matching event_id"""
    # User login required
    if 'username' not in flask.session:
        # Store current page to redirect back to after login
        flask.session['prelogin_page'] = flask.url_for(
                                             'update_event',
                                             activity_id=activity_id,
                                             event_id=event_id)
        return flask.redirect('/login/')

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
        event = set_event_fields(event)
        with db_session() as db:
            db.add(event)
            db.commit()
            return flask.redirect(
                       flask.url_for('display_event',
                                     activity_id=activity_id,
                                     event_id=event.id))
    else:
        return flask.render_template('edit-event.html',
                                     activity=activity,
                                     event=event)


@app.route('/activities/<int:activity_id>/events/<int:event_id>/delete/',
           methods=['GET', 'POST'])
@entry_and_exit_logger
def delete_event(activity_id, event_id):
    """Delete Event record in DB with matching event_id"""
    # User login required
    if 'username' not in flask.session:
        # Store current page to redirect back to after login
        flask.session['prelogin_page'] = flask.url_for(
                                             'delete_event',
                                             activity_id=activity_id,
                                             event_id=event_id)
        return flask.redirect('/login/')

    with db_session() as db:
        activity = db.query(models.Activity) \
                     .filter_by(id=activity_id) \
                     .one()
        event = db.query(models.Event) \
                  .filter_by(id=event_id,
                             activity_id=activity_id) \
                  .one()

    # Event can only be deleted by its owner
    if event.user_id != get_user_id(user_email=flask.session['email']):
        return flask.redirect(
                   flask.url_for('display_event',
                                 activity_id=activity.id,
                                 event_id=event.id))

    if flask.request.method == 'POST':
        with db_session() as db:
            db.delete(event)
            db.commit()
        return flask.redirect(
                   flask.url_for('display_activity',
                                 activity_id=activity_id))

    else:
        return flask.render_template('delete-event.html',
                                     activity=activity,
                                     event=event)


@entry_and_exit_logger
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
    new_user = models.UserAccount(name=session['username'],
                                  email=session['email'],
                                  picture=session['picture'])
    with db_session() as db:
        db.add(new_user)
        db.commit()
        user = db.query(models.UserAccount) \
                 .filter_by(email=session['email']) \
                 .one()
    return user.id


@entry_and_exit_logger
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
    with db_session() as db:
        user = db.query(models.UserAccount) \
                 .filter_by(id=user_id) \
                 .one()
    return user


@entry_and_exit_logger
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
        return user.id
    except:
        return None


@app.route('/activities/JSON/')
@entry_and_exit_logger
def activities_endpoint():
    """Returns a JSON endpoint for all activities"""
    activities = []
    with db_session() as db:
        for activity in db.query(models.Activity).all():
            activity = activity.serialize
            activity['events'] = [event.serialize for event in
                                  db.query(models.Event)
                                    .filter_by(activity_id=activity['id'])
                                    .all()]
            activities.append(activity)

    if activities:
        return flask.jsonify(activities)

    else:
        app.logger.error(
            ('activities_endpoint() - -'
             '    [NO Activities FOUND]'))
        return flask.jsonify({
                              'status': 404,
                              'error': 'No Activities found',
                             })


@app.route('/activities/<int:activity_id>/events/JSON/')
@entry_and_exit_logger
def activity_endpoint(activity_id):
    """Returns a JSON endpoint for an activity"""
    try:
        with db_session() as db:
            activity = db.query(models.Activity) \
                         .filter_by(id=activity_id) \
                         .one()
    except:
        app.logger.error(
            ('activity_endpoint() - -'
             '    [NOT FOUND: activity_id={}]'.format(activity_id)))
        return flask.jsonify({
                              'status': 404,
                              'error': 'Activity not found',
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
@entry_and_exit_logger
def event_endpoint(activity_id, event_id):
    """Returns a JSON endpoint for an event"""
    try:
        with db_session() as db:
            event = db.query(models.Event) \
                      .filter_by(id=event_id) \
                      .one()
    except:
        app.logger.error(
            ('event_endpoint() - -'
             '    [NOT FOUND: event_id={}]'.format(event_id)))
        return flask.jsonify({
                              'status': 404,
                              'error': 'Event not found',
                             })
    else:
        return flask.jsonify(event.serialize)


if __name__ == '__main__':
    """Setup logging and run app"""
#    file_handler = logging.handlers.RotatingFileHandler(
#                       'APP_{}.log'.format(timestamp_gen(file_ext=True)),
#                       maxBytes=16384,
#                       backupCount=4)
#    file_formatter = logging.Formatter('{levelname:9} {name:10} {message}',
#                                        style='{')
#    file_handler.setFormatter(file_formatter)
#    file_handler.setLevel(logging.DEBUG)
#    app.logger.addHandler(file_handler)

    app.debug = True
    app.secret_key = 'PLACEHOLDER FOR DEV TESTING'
    app.run(host='0.0.0.0', port=5000)
