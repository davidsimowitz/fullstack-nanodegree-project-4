from flask import Flask, redirect, render_template, request, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Activity, Base, DB, Event

import datetime, re
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps


app = Flask(__name__)

engine = create_engine(DB)
Base.metadata.bind = engine

create_session = sessionmaker(bind=engine)
session = create_session()


def entry_and_exit_logger(func):
    """
    prints function input arguments to logger
    when entering and exiting decorated function
    """
    @wraps(func)
    def entry_and_exit_wrapper(*args, **kwargs):
        """log wrapper"""
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
    """
    for file extensions, generate the current time
    <YYYY-MM-DD_HH:MM:SS.ssssss> format as str.

    for logging, generate in <Weekday Month DD HH:MM:SS YYYY> format.
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
    """ parse str_input and return date match """
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
    """ parse str_input and return date match """
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
    """ check date to verify it is acceptable """
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
    """ check date to verify it is acceptable """
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
    """
    checks date values
    """
    date = parse_date(date)
    date = verify_date(date)

    return date


@entry_and_exit_logger
def time_checker(time):
    """
    checks time values
    """
    time = parse_time(time)
    time = verify_time(time)

    return time

@entry_and_exit_logger
def set_event_fields(event):
    """Use in a POST method to return an updated Event obj"""
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
    """Display activities"""
    activities = session.query(Activity)
    return render_template('activities.html', activities=activities)

@app.route('/login/')
@entry_and_exit_logger
def login():
    """Login"""
    return 'login'


@app.route('/activities/<int:activity_id>/')
@app.route('/activities/<int:activity_id>/events/')
@entry_and_exit_logger
def display_activity(activity_id):
    """Get activity"""
    activity = session.query(Activity).filter_by(id=activity_id).one()
    events = session.query(Event).filter_by(activity_id=activity_id).all()
    return render_template('events.html', activity=activity, events=events)


@app.route('/activities/new/', methods=['GET', 'POST'])
@entry_and_exit_logger
def make_activity():
    """Create activity"""
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
    """Edit activity"""
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
    """Delete activity"""
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
    """Display event"""
    activity = session.query(Activity).filter_by(id=activity_id).one()
    event = session.query(Event).filter_by(id=event_id,
                                           activity_id=activity_id).one()
    return render_template('event.html', activity=activity, event=event)


@app.route('/activities/<int:activity_id>/events/new/',
           methods=['GET', 'POST'])
@entry_and_exit_logger
def make_event(activity_id):
    """Create event"""
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
    """Edit event"""
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
    """Delete event"""
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
    file_handler = RotatingFileHandler('APP_{}.log'.format(timestamp_gen(file_ext=True)),
                                          maxBytes=16384,
                                          backupCount=4)
    file_formatter = logging.Formatter('{levelname:9} {name:10} {message}', style='{')
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)

    app.debug = True
    app.run(host='0.0.0.0', port=5000)
