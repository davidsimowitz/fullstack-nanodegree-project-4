from flask import Flask, redirect, render_template, request, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Activity, Base, DB, Event

import datetime, re
import logging
from logging.handlers import RotatingFileHandler


app = Flask(__name__)

engine = create_engine(DB)
Base.metadata.bind = engine

create_session = sessionmaker(bind=engine)
session = create_session()


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


def date_checker(date):
    """
    checks date values
    """
    date = parse_date(date)
    date = verify_date(date)

    return date


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
        event.start_time = request.form['start_time']
    if request.form['end_date']:
        end_date = request.form['end_date']
        end_date = date_checker(end_date)
        if end_date:
            event.end_date = end_date
    if request.form['end_time']:
        event.end_time = request.form['end_time']
    return event


@app.route('/')
@app.route('/activities/')
def display_activities():
    """Display activities"""
    activities = session.query(Activity)
    return render_template('activities.html', activities=activities)


@app.route('/login/')
def login():
    """Login"""
    return 'login'


@app.route('/activities/<int:activity_id>/')
@app.route('/activities/<int:activity_id>/events/')
def display_activity(activity_id):
    """Get activity"""
    activity = session.query(Activity).filter_by(id=activity_id).one()
    events = session.query(Event).filter_by(activity_id=activity_id).all()
    return render_template('events.html', activity=activity, events=events)


@app.route('/activities/new/', methods=['GET', 'POST'])
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
def display_event(activity_id, event_id):
    """Display event"""
    activity = session.query(Activity).filter_by(id=activity_id).one()
    event = session.query(Event).filter_by(id=event_id,
                                           activity_id=activity_id).one()
    return render_template('event.html', activity=activity, event=event)


@app.route('/activities/<int:activity_id>/events/new/',
           methods=['GET', 'POST'])
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
