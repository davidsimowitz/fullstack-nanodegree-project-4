from flask import Flask, render_template
app = Flask(__name__)


@app.route('/')
@app.route('/activities/')
def display_activities():
    """Display activities"""
    test = [{'title':'Camp David', 'description':'Hiking and relaxing outdoors under the stars', 'date':'09-16-2017'}, {'title':'Halloween Party', 'description':'Costume contest and snacks', 'date':'10-31-2017'}, {'title':'Birthday Party!', 'description':'Celebrate my 35th birthday!', 'date':'11-27-2017'}]
    return render_template('activities.html', title='Activities', events=test)


@app.route('/login/')
def login():
    """Login"""
    return 'login'


@app.route('/activities/<int:activity_id>/')
@app.route('/activities/<int:activity_id>/events/')
def display_activity(activity_id):
    """Get activity"""
    return 'display activity {}'.format(activity_id)


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
    return 'display event {} for activity {}'.format(event_id, activity_id)


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
