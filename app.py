from flask import Flask, redirect, render_template, request, url_for
from flask import session as login_session
from models import Activity, Base, DB, Event

import datetime, random, re, string
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps

import oauth2client.client
import httplib2
import json
from flask import make_response
import requests
import sqlalchemy


CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']

app = Flask(__name__)

engine = sqlalchemy.create_engine(DB)
Base.metadata.bind = engine

create_session = sqlalchemy.orm.sessionmaker(bind=engine)
session = create_session()


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
    @wraps(func)
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

        message = '[{timestamp}] - - {action:8} {arguments}'
        func_params = {'arguments': '{}({})'.format(func.__name__, arguments),
                       'timestamp': datetime.datetime.now().ctime(),
                       'action': 'ENTER'}
        app.logger.debug(message.format(**func_params))

        result = func(*args, **kwargs)

        func_params['arguments'] = '{}({}={})'.format(func.__name__,
                                                      'result', result)
        func_params['timestamp'] = datetime.datetime.now().ctime()
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
    patterns = ['(?P<year>[\d]{4})[-/]?' \
                '(?P<month>[\d]{1,2})[-/]?' \
                '(?P<day>[\d]{1,2})', #YYYY_MM_DD
                '(?P<month>[\d]{1,2})[-/]?' \
                '(?P<day>[\d]{1,2})[-/]?' \
                '(?P<year>[\d]{4})', #MM_DD_YYYY
                '(?P<month>' + _MONTHS + '){1}\s' \
                '(?P<day>[\d]{1,2})\,?\s(?P<year>[\d]{4})'] #MONTH_DD_YYYY

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
    patterns = ['(?P<hours>[\d]{1,2})[:]{1}' \
                '(?P<minutes>[\d]{2})[:]{1}' \
                '(?P<seconds>[\d]{2})' \
                '(?P<timezone>[+-]?[\d]{2}[:]{1}[\d]{2})', #HH:MM:SS(+/-)TT:TT
                '(?P<hours>[\d]{1,2})[:]{1}' \
                '(?P<minutes>[\d]{2})[:]{1}' \
                '(?P<seconds>[\d]{2})\s?' \
                '(?P<twelve_hr>am|pm|a\.m\.|p\.m\.){1}', #HH:MM:SS (AM/PM)
                '(?P<hours>[\d]{1,2})[:]{1}' \
                '(?P<minutes>[\d]{2})\s?' \
                '(?P<twelve_hr>am|pm|a\.m\.|p\.m\.){1}', #HH:MM (AM/PM)
                '(?P<hours>[\d]{1,2})[:]{1}' \
                '(?P<minutes>[\d]{2})[:]{1}' \
                '(?P<seconds>[\d]{2})', #HH:MM:SS (24-hour notation)
                '(?P<hours>[\d]{1,2})[:]{1}' \
                '(?P<minutes>[\d]{2})'] #HH:MM (24-hour notation)
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
    if request.form['name']:
        event.name = request.form['name']
    if request.form['description']:
        event.description = request.form['description']
    if request.form['start_date']:
        start_date = request.form['start_date']
        start_date = date_checker(start_date)
        if start_date:
            event.start_date = start_date
    if request.form['start_time']:
        start_time = request.form['start_time']
        start_time = time_checker(start_time)
        if start_time:
            event.start_time = start_time
    if request.form['end_date']:
        end_date = request.form['end_date']
        end_date = date_checker(end_date)
        if end_date:
            event.end_date = end_date
    if request.form['end_time']:
        end_time = request.form['end_time']
        end_time = time_checker(end_time)
        if end_time:
            event.end_time = end_time
    return event


@app.route('/')
@app.route('/activities/')
@entry_and_exit_logger
def display_activities():
    """Display all Activity records from DB."""
    activities = session.query(Activity)
    return render_template('activities.html', activities=activities)


@app.route('/login/')
@entry_and_exit_logger
def user_login():
    """Create an anti-forgery state token and store it in the session"""
    state = ''.join(random.choice(string.ascii_letters + string.digits)
                    for x in range(64))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/google.connect/', methods=['POST'])
@entry_and_exit_logger
def google_connect():
    """OAuth via Google"""
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(
                       json.dumps('Invalid state parameter'),
                       401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

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
        response = make_response(json.dumps('Format of ClientSecrets' +
                                            ' file is invalid.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    except oauth2client.client.FlowExchangeError:
        # Error trying to exchange an authorization grant for an access token.
        response = make_response(json.dumps('Error trying to exchange an' +
                                            ' authorization grant for an' +
                                            ' access token.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    http = httplib2.Http()
    result = json.loads(str(http.request(url, 'GET')[1], 'utf-8'))

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')),
                                 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    user_id = credentials.id_token['sub']
    if result['user_id'] != user_id:
        response = make_response(json.dumps("Token's user ID does not match" +
                                            " given user ID."),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response


    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
                       json.dumps("Token's client ID does not match app's."),
                       401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_user_id = login_session.get('user_id')
    if stored_access_token is not None and user_id == stored_user_id:
        response = make_response(
                       json.dumps('Current user is already connected.'),
                       200)
        response.headers['Content-Type'] = 'application/json'
        return response


    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['user_id'] = user_id

    # Get user info
    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'

    output += '<img src="'
    output += login_session['picture']
    output += '" style="max-width: 325px; height: auto;">'

    return output


@app.route('/activities/<int:activity_id>/')
@app.route('/activities/<int:activity_id>/events/')
@entry_and_exit_logger
def display_activity(activity_id):
    """Display Activity record from DB with matching activity_id.

    Display Activity and list all Event records corresponding to it.
    """
    activity = session.query(Activity).filter_by(id=activity_id).one()
    events = session.query(Event).filter_by(activity_id=activity_id).all()
    return render_template('events.html', activity=activity, events=events)


@app.route('/activities/new/', methods=['GET', 'POST'])
@entry_and_exit_logger
def make_activity():
    """Create new Activity record in DB"""
    if request.method == 'POST':
        new_activity = Activity(name=request.form['name'])
        session.add(new_activity)
        session.commit()

        return redirect(url_for('display_activity',
                                activity_id=new_activity.id))
    else:
        return render_template('new-activity.html')


@app.route('/activities/<int:activity_id>/edit/', methods=['GET', 'POST'])
@entry_and_exit_logger
def update_activity(activity_id):
    """Update Activity record in DB with matching activity_id"""
    activity = session.query(Activity).filter_by(id=activity_id).one()

    if request.method == 'POST':
        if request.form['name']:
            activity.name = request.form['name']
        session.add(activity)
        session.commit()

        return redirect(url_for('display_activity',
                                activity_id=activity.id))
    else:
        return render_template('edit-activity.html',
                               activity=activity)


@app.route('/activities/<int:activity_id>/delete/', methods=['GET', 'POST'])
@entry_and_exit_logger
def delete_activity(activity_id):
    """Delete Activity record in DB with matching activity_id"""
    activity = session.query(Activity).filter_by(id=activity_id).one()

    if request.method == 'POST':
        events = session.query(Event).filter_by(activity_id=activity_id).all()
        if events:
            error_msg = 'Activity cannot be deleted, events ' \
                        'are associated with this activity.'
            return render_template('delete-activity.html',
                                    activity=activity,
                                    error_msg=error_msg)
        else:
            session.delete(activity)
            session.commit()
            return redirect(url_for('display_activities'))

    else:
        return render_template('delete-activity.html',
                               activity=activity)


@app.route('/activities/<int:activity_id>/events/<int:event_id>/')
@entry_and_exit_logger
def display_event(activity_id, event_id):
    """Display Event record from DB with matching event_id"""
    activity = session.query(Activity).filter_by(id=activity_id).one()
    event = session.query(Event).filter_by(id=event_id,
                                           activity_id=activity_id).one()
    return render_template('event.html', activity=activity, event=event)


@app.route('/activities/<int:activity_id>/events/new/',
           methods=['GET', 'POST'])
@entry_and_exit_logger
def make_event(activity_id):
    """Create new Event record in DB"""
    if request.method == 'POST':
        new_event = Event(name=request.form['name'],
                          activity_id=activity_id)
        new_event = set_event_fields(new_event)
        session.add(new_event)
        session.commit()
        return redirect(url_for('display_event',
                                activity_id=activity_id,
                                event_id=new_event.id))
    else:
        activity = session.query(Activity).filter_by(id=activity_id).one()
        return render_template('new-event.html', activity=activity)


@app.route('/activities/<int:activity_id>/events/<int:event_id>/edit/',
           methods=['GET', 'POST'])
@entry_and_exit_logger
def update_event(activity_id, event_id):
    """Update Event record in DB with matching event_id"""
    activity = session.query(Activity).filter_by(id=activity_id).one()
    event = session.query(Event).filter_by(id=event_id,
                                           activity_id=activity_id).one()

    if request.method == 'POST':
        event = set_event_fields(event)
        session.add(event)
        session.commit()
        return redirect(url_for('display_event',
                                activity_id=activity_id,
                                event_id=event.id))
    else:
        return render_template('edit-event.html',
                               activity=activity,
                               event=event)


@app.route('/activities/<int:activity_id>/events/<int:event_id>/delete/',
           methods=['GET', 'POST'])
@entry_and_exit_logger
def delete_event(activity_id, event_id):
    """Delete Event record in DB with matching event_id"""
    activity = session.query(Activity).filter_by(id=activity_id).one()
    event = session.query(Event).filter_by(id=event_id,
                                           activity_id=activity_id).one()

    if request.method == 'POST':
        session.delete(event)
        session.commit()
        return redirect(url_for('display_activity', activity_id=activity_id))

    else:
        return render_template('delete-event.html',
                               activity=activity,
                               event=event)


if __name__ == '__main__':
    """Setup logging and run app"""
    #file_handler = RotatingFileHandler('APP_{}.log'.format(timestamp_gen(file_ext=True)),
    #                                      maxBytes=16384,
    #                                      backupCount=4)
    #file_formatter = logging.Formatter('{levelname:9} {name:10} {message}', style='{')
    #file_handler.setFormatter(file_formatter)
    #file_handler.setLevel(logging.DEBUG)
    #app.logger.addHandler(file_handler)

    screen_handler = logging.StreamHandler()
    screen_formatter = logging.Formatter('{levelname:9} {name:10} {message}', style='{')
    screen_handler.setFormatter(screen_formatter)
    screen_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(screen_handler)

    app.debug = True
    app.secret_key = 'PLACEHOLDER FOR DEV TESTING'
    app.run(host='0.0.0.0', port=5000)
