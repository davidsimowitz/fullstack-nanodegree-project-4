from flask import Flask, redirect, render_template, request, url_for
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
                          description=request.form['description'],
                          start_date=request.form['start_date'],
                          start_time=request.form['start_time'],
                          end_date=request.form['end_date'],
                          end_time=request.form['end_time'],
                          activity_id=activity_id)
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
        if request.form['name']:
            event.name = request.form['name']
        if request.form['description']:
            event.description = request.form['description']
        if request.form['start_date']:
            event.start_date = request.form['start_date']
        if request.form['start_time']:
            event.start_time = request.form['start_time']
        if request.form['end_date']:
            event.end_date = request.form['end_date']
        if request.form['end_time']:
            event.end_time = request.form['end_time']
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
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
