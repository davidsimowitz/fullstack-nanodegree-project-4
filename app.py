from flask import Flask, render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Activity, Base, DB, Event


app = Flask(__name__)

engine = create_engine(DB)
Base.metadata.bind = engine

create_session = sessionmaker(bind=engine)
session = create_session()


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


@app.route('/activities/new/')
def make_activity():
    """Create activity"""
    return 'make activity'


@app.route('/activities/<int:activity_id>/edit/')
def update_activity(activity_id):
    """Edit activity"""
    return 'update activity {}'.format(activity_id)


@app.route('/activities/<int:activity_id>/delete/')
def delete_activity(activity_id):
    """Delete activity"""
    return 'delete activity {}'.format(activity_id)


@app.route('/activities/<int:activity_id>/events/<int:event_id>/')
def display_event(activity_id, event_id):
    """Display event"""
    event = session.query(Event).filter_by(id=event_id,
                                           activity_id=activity_id).one()
    return render_template('event.html', event=event)


@app.route('/activities/<int:activity_id>/events/new/')
def make_event(activity_id):
    """Create event"""
    return 'make event for activity {}'.format(activity_id)


@app.route('/activities/<int:activity_id>/events/<int:event_id>/edit/')
def update_event(activity_id, event_id):
    """Edit event"""
    return 'update event {} for activity {}'.format(event_id, activity_id)


@app.route('/activities/<int:activity_id>/events/<int:event_id>/delete/')
def delete_event(activity_id, event_id):
    """Delete event"""
    return 'delete event {} for activity {}'.format(event_id, activity_id)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
