#!/usr/bin/env python3
"""
populate events database with test data
"""


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Activity, Base, Event


DB = 'postgresql:///events.db'


def create_activities(session):
    """create and commit entries to the activity table"""

    activities = ['outdoors', 'fitness', 'games', 'music', 'film', 'food',
                  'drink', 'shopping']
    for activity in activities:
        new_entry = Activity(name='{}'.format(activity.lower()))
        session.add(new_entry)
        session.commit()


def create_events(session):
    """create and commit entries to the event table"""

    event_lookup = {}
    event_lookup['outdoors'] = ['camping', 'hiking', 'beach', 'park']
    event_lookup['fitness'] = ['saturday morning group run', 'biking',
                               'swimming', 'walking in the park']
    event_lookup['games'] = ['game day', 'board game night', 'US Open']
    event_lookup['music'] = ['concert']
    event_lookup['film'] = ['movies']
    event_lookup['food'] = ['birthday dinner', 'Brooklyn Bridge Park BBQ']
    event_lookup['drink'] = ['happy hour']
    event_lookup['shopping'] = ['back to school sale']

    activities = session.query(Activity)

    for activity_entry in activities:
        events = event_lookup[activity_entry.name]

        for event in events:
            new_event = Event(name='{}'.format(event), activity=activity_entry)
            session.add(new_event)
            session.commit()


def initialize_db(session):
    """setup events.db database with test records"""

    create_activities(session)
    create_events(session)


def print_activities(session):
    """print activity table records"""

    activities = session.query(Activity)
    print('\nActivities: ')
    for activity in activities:
        print(activity.name.title())


def print_events(session):
    """print event table records"""

    events = session.query(Event)
    print('\nEvents: ')
    for event in events:
        activity = session.query(Activity).filter_by(id=event.activity_id).one()
        print('{} -> {}'.format(activity.name.title(), event.name))


def print_db(session):
    """print database records"""

    print_activities(session)
    print_events(session)


def main():
    """populate events database with test data"""

    engine = create_engine(DB)
    Base.metadata.bind = engine

    create_session = sessionmaker(bind=engine)
    session = create_session()

    #initialize_db(session)
    print_db(session)


if __name__ == '__main__':
    main()
