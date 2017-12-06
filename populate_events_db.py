#!/usr/bin/env python3
"""
populate events database with test data
"""


import sqlalchemy
import sqlalchemy.orm
from models import Activity, Base, DB, Event


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
    event_lookup['outdoors'] = [
        ('camping', '2017-10-6', '18:30', '2017-10-8', '10:45'),
        ('hiking', '2017-10-7', '11:45', '2017-10-7', '17:00'),
        ('beach', '2017-10-14', '8:30', '2017-10-14', '15:15'),
        ('park', '2017-10-21', '2:15', '2017-10-21', '6:00')]
    event_lookup['fitness'] = [
        ('saturday morning group run', '2017-9-30', '7:00', '2017-9-30',
         '9:00'),
        ('biking', '2017-10-17', '18:30', '2017-10-17', '19:30'),
        ('swimming', '2017-8-19', '10:15', '2017-8-19', '12:15'),
        ('walking in the park', '2017-10-19', '17:45', '2017-10-19', '18:15')]
    event_lookup['games'] = [
        ('game day', '2017-10-22', '13:15', '2017-10-22', '19:45'),
        ('board game night', '2017-10-14', '17:00', '2017-10-14', '23:00'),
        ('US Open', '2017-8-28', '00:00', '2017-9-1', '23:59')]
    event_lookup['music'] = [
        ('concert', '2017-11-3', '20:00', '2017-11-3', '24:00')]
    event_lookup['film'] = [
        ('movies', '2017-12-15', '18:00', '2017-12-15', '20:45')]
    event_lookup['food'] = [
        ('birthday dinner', '2017-11-25', '18:45', '2017-11-25', '21:45'),
        ('Brooklyn Bridge Park BBQ', '2017-10-27', '18:15', '2017-10-27',
         '19:30')]
    event_lookup['drink'] = [
        ('happy hour', '2017-10-26', '17:00', '2017-10-26', '18:00')]
    event_lookup['shopping'] = [
        ('back to school sale', '2017-8-14', '00:00', '2017-8-28', '23:59')]

    activities = session.query(Activity)

    for activity_entry in activities:
        events = event_lookup[activity_entry.name]

        for event in events:
            new_event = Event(
                          name='{}'.format(event[0]),
                          activity=activity_entry,
                          description='{} event description.'.format(event[0]),
                          start_date='{}'.format(event[1]),
                          start_time='{}'.format(event[2]),
                          end_date='{}'.format(event[3]),
                          end_time='{}'.format(event[4]))
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
        activity = session.query(Activity).filter_by(
                     id=event.activity_id).one()
        print('{} -> {}:\n          {}\n          start: {} {}' +
              '\n          end:   {} {}'.format(activity.name.title(),
                                                event.name,
                                                event.description,
                                                event.start_date,
                                                event.start_time,
                                                event.end_date,
                                                event.end_time))


def print_db(session):
    """print database records"""

    print_activities(session)
    print_events(session)


def main():
    """populate events database with test data"""

    engine = sqlalchemy.create_engine(DB)
    Base.metadata.bind = engine

    create_session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = create_session()

    # initialize_db(session)
    print_db(session)


if __name__ == '__main__':
    main()
