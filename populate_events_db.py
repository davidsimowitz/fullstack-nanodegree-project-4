#!/usr/bin/env python3
"""
populate events database with test data
"""


import collections
import contextlib
import models
import sqlalchemy
import sqlalchemy.orm


engine = sqlalchemy.create_engine(models.DB)
models.declarative_base.metadata.bind = engine
create_sqlalchemy_session = sqlalchemy.orm.sessionmaker(bind=engine)


@contextlib.contextmanager
def db_session(message=None):
    db = create_sqlalchemy_session()
    try:
        yield db
    except:
        print("error: {}".format(message))
        db.rollback()
        raise
    finally:
        db.close()


ADMIN_EMAIL = "david.simowitz@gmail.com"

User = collections.namedtuple(
                      'User',
                      ['name', 'email', 'picture']
                      )
Activity = collections.namedtuple(
                          'Activity',
                          ['name', 'icon', 'user_id']
                          )
Event = collections.namedtuple(
                       'Event',
                       ['name', 'description',
                        'start_date', 'start_time',
                        'end_date', 'end_time',
                        'user_id', 'activity_id']
                       )


def create_admin():
    """creat site admin"""
    admin_user = User(
                     "David Simowitz",
                     "david.simowitz@gmail.com",
                     "https://lh6.googleusercontent.com/-bO6Jr_RkpXw" \
                     "/AAAAAAAAAAI/AAAAAAAACXQ/4ykCbz_oqF8/photo.jpg"
                     )
    message = "create_admin(): {}".format(admin_user)
    with db_session(message) as db:
        new_user = models.UserAccount(
                             name=admin_user.name,
                             email=admin_user.email,
                             picture=admin_user.picture
                             )
        db.add(new_user)
        db.commit()


def get_admin_id():
    message="get_admin_id()"
    with db_session(message) as db:
        admin = db.query(models.UserAccount) \
                  .filter_by(email=ADMIN_EMAIL) \
                  .one()
        return admin.id


def create_activities():
    """create and commit entries to the activity table"""
    user_id = get_admin_id()
    activities = []

    new_activity = Activity(
                       "swimming",
                       "/static/img/waves-icon.svg",
                       user_id
                       )
    activities.append(new_activity)

    new_activity = Activity(
                       "beach",
                       "/static/img/towel-on-sand-icon.svg",
                       user_id
                       )
    activities.append(new_activity)

    new_activity = Activity(
                       "movies",
                       "/static/img/popcorn-and-soda-icon.svg",
                       user_id
                       )
    activities.append(new_activity)

    new_activity = Activity(
                       "music",
                       "/static/img/music-note-icon.svg",
                       user_id
                       )
    activities.append(new_activity)

    new_activity = Activity(
                       "hiking",
                       "/static/img/tree-icon.svg",
                       user_id
                       )
    activities.append(new_activity)

    new_activity = Activity(
                       "BBQ",
                       "/static/img/burger-icon.svg",
                       user_id
                       )
    activities.append(new_activity)

    new_activity = Activity(
                       "drinks",
                       "/static/img/wine-glasses-icon.svg",
                       user_id
                       )
    activities.append(new_activity)

    new_activity = Activity(
                       "Coney Island",
                       "/static/img/hotdog-icon.svg",
                       user_id
                       )
    activities.append(new_activity)

    new_activity = Activity(
                       "outdoors",
                       "/static/img/sun-icon.svg",
                       user_id
                       )
    activities.append(new_activity)

    new_activity = Activity(
                       "camping",
                       "/static/img/tent-icon.svg",
                       user_id
                       )
    activities.append(new_activity)

    new_activity = Activity(
                       "boating",
                       "/static/img/sail-boat-icon.svg",
                       user_id
                       )
    activities.append(new_activity)

    new_activity = Activity(
                       "arts & film",
                       "/static/img/film-camera-icon.svg",
                       user_id
                       )
    activities.append(new_activity)

    for activity in activities:
        message = "create_activities(): {}".format(activity)
        with db_session(message) as db:
            new_activity = models.Activity(
                                     name=activity.name,
                                     icon=activity.icon,
                                     user_id=activity.user_id
                                     )
            db.add(new_activity)
            db.commit()


def create_events():
    """create and commit entries to the event table"""
    OWNER_ID = 1
    events = list()

    def recurring_event(*, calendar_start, calendar_end, interval="1 day"):
        message = "recurring_event(calendar_start={}, calendar_end={}," \
                  "interval={})".format(calendar_start, calendar_end, interval)
        with db_session(message) as db:
            dates = db.query(
                sqlalchemy.func.generate_series(
                    calendar_start,
                    calendar_end,
                    sqlalchemy.text("'{}'::interval".format(interval))
                    )
                    .cast(sqlalchemy.Date)
                    .label('event_date')
                    )
            return dates

    def insert_event(event_record):
        """insert event into table"""
        if isinstance(event_record, tuple):
            message = "create_events(): {}".format(event_record)
            with db_session(message) as db:
                new_event = models.Event(
                                name=event_record.name,
                                description=event_record.description,
                                start_date=event_record.start_date,
                                _start_time=event_record.start_time,
                                end_date=event_record.end_date,
                                _end_time=event_record.end_time,
                                user_id=event_record.user_id,
                                activity_id=event_record.activity_id
                                )
                db.add(new_event)
                db.commit()
        else:    
            for event in event_record:
                message = "create_events(): {}".format(event)
                with db_session(message) as db:
                    new_event = models.Event(
                                    name=event.name,
                                    description=event.description,
                                    start_date=event.start_date,
                                    _start_time=event.start_time,
                                    end_date=event.end_date,
                                    _end_time=event.end_time,
                                    user_id=event.user_id,
                                    activity_id=event.activity_id
                                    )
                    db.add(new_event)
                    db.commit()

    #swimming events
    message = "create_events(): {}".format("lookup swimming activity")
    with db_session(message) as db:
        swimming = db.query(models.Activity) \
                     .filter_by(name="swimming") \
                     .one()

    events.clear()
    for date in recurring_event(calendar_start='2018-6-27',
                                calendar_end='2018-9-21'):
        new_event = Event(
            "Brooklyn Bridge Park Pop-Up Pool",
            "Take a dip in one of New York City's coolest hidden " \
            "gems, then relax on the beach after your swim.\nhttps" \
            "://www.brooklynbridgepark.org/attractions/pop-up-pool\n" \
            "Address: Brooklyn Bridge Park: Pier 2\n" \
            "150 Furman St, Brooklyn, NY 11201",
            date.event_date,
            "10:00",
            date.event_date,
            "18:00",
            get_admin_id(),
            swimming.id
            )
        print(new_event)
        events.append(new_event)
    print(events)
    insert_event(events)

    #beach events
    message = "create_events(): {}".format("lookup beach activity")
    with db_session(message) as db:
        beach = db.query(models.Activity) \
                  .filter_by(name="beach") \
                  .one()

    #movies events
    message = "create_events(): {}".format("lookup movies activity")
    with db_session(message) as db:
        movies = db.query(models.Activity) \
                   .filter_by(name="movies") \
                   .one()

    new_event = Event(
        "BlacKkKlansman (premier)",
        "From visionary filmmaker Spike Lee comes the incredible true " \
        "story of an American hero. It's the early 1970s, and Ron " \
        "Stallworth (John David Washington) is the first African-American " \
        "detective to serve in the Colorado Springs Police Department. " \
        "Determined to make a name for himself, Stallworth bravely sets " \
        "out on a dangerous mission: infiltrate and expose the Ku Klux " \
        "Klan. The young detective soon recruits a more seasoned " \
        "colleague, Flip Zimmerman (Adam Driver), into the undercover " \
        "investigation of a lifetime. Together, they team up to take " \
        "down the extremist hate group as the organization aims to " \
        "sanitize its violent rhetoric to appeal to the mainstream. " \
        "Produced by the team behind the Academy-Award® winning Get Out.\n\n" \
        "http://www.focusfeatures.com/blackkklansman",
        "2018-8-10",
        "19:00",
        "2018-8-10",
        None,
        get_admin_id(),
        movies.id
        )
    insert_event(new_event)

    new_event = Event(
        "Venom (premier)",
        "One of Marvel's most enigmatic, complex and badass characters " \
        "comes to the big screen, starring Academy Award® nominated " \
        "actor Tom Hardy as the lethal protector Venom.\n\n" \
        "http://www.venom.movie/site/",
        "2018-10-5",
        None,
        "2018-10-5",
        None,
        get_admin_id(),
        movies.id
        )
    insert_event(new_event)

    new_event = Event(
        "FIRST MAN (premier)",
        "The riveting story of NASA's mission to land a man on the " \
        "moon, focusing on Neil Armstrong and the years 1961-1969, " \
        "and explores the sacrifices and the cost-on Armstrong and on " \
        "the nation-of one of the most dangerous missions in history.\n\n" \
        "https://www.firstman.com/",
        "2018-10-12",
        None,
        "2018-10-12",
        None,
        get_admin_id(),
        movies.id
        )
    insert_event(new_event)

    #music events
    message = "create_events(): {}".format("lookup music activity")
    with db_session(message) as db:
        music = db.query(models.Activity) \
                  .filter_by(name="music") \
                  .one()

    #Doctors Orchestra concerts
    events.clear()
    new_event = Event(
        "DOCTORS ORCHESTRA",
        "Bizet Jeux d'Enfant Suite, Mozart Flute Concerto, Cesar Frank " \
        "Symphony in D minor\n\nhttp://www.doctorsorchestra.org/",
        "2018-10-18",
        "19:30",
        "2018-10-18",
        "21:30",
        get_admin_id(),
        music.id
        )
    events.append(new_event)

    new_event = Event(
        "DOCTORS ORCHESTRA",
        "Wagner Tannhauser Overture, Chopin Piano Concerto No. 2 in F " \
        "minor, Shostakovich Symphony No. 1 in F minor\n" \
        "http://www.doctorsorchestra.org/",
        "2018-12-20",
        "19:30",
        "2018-12-20",
        "21:30",
        get_admin_id(),
        music.id
        )
    events.append(new_event)

    new_event = Event(
        "DOCTORS ORCHESTRA",
        "Grieg Peer Gynt Suite No. 1, M. Bruch Violin Concerto No. 1 in " \
        "G minor, Gliere Bronze Horseman Suite\n" \
        "http://www.doctorsorchestra.org/",
        "2019-2-28",
        "19:30",
        "2019-2-28",
        "21:30",
        get_admin_id(),
        music.id
        )
    events.append(new_event)

    new_event = Event(
        "DOCTORS ORCHESTRA",
        "F. Delius In a Summer Garden, Saint-Saens Cello Concerto No. 1 in A " \
        "minor, Rimsky Korsakov Scheherazade\n\n" \
        "http://www.doctorsorchestra.org/",
        "2019-5-14",
        "19:30",
        "2019-5-14",
        "21:30",
        get_admin_id(),
        music.id
        )
    events.append(new_event)
    insert_event(events)

    events.clear()
    for date in recurring_event(calendar_start='2018-6-27',
                                calendar_end='2018-9-21'):
        new_event = Event(
            "Bargemusic",
            "Walk across the gangplank of a renovated coffee barge for a " \
            "one-hour, family-friendly concert.\n"
            "Visit Bargemusic for their free Neighborhood Family Concerts. " \
            "This one-hour performance includes a Q & A session with the " \
            "musicians. Doors open 15 minutes before the performance - no " \
            "reserved seating is available. Visit bargemusic.org for more!\n" \
            "Location: Brooklyn Bridge Park: Pier 1\n" \
            "Brooklyn Bridge Blvd, Brooklyn, NY 11201",
            date.event_date,
            "10:00",
            date.event_date,
            "18:00",
            get_admin_id(),
            music.id
            )
        events.append(new_event)
    insert_event(events)

    #hiking events
    message = "create_events(): {}".format("lookup hiking activity")
    with db_session(message) as db:
        hiking = db.query(models.Activity) \
                   .filter_by(name="hiking") \
                   .one()

    #BBQ events
    message = "create_events(): {}".format("lookup BBQ activity")
    with db_session(message) as db:
        bbq = db.query(models.Activity) \
                .filter_by(name="BBQ") \
                .one()

    new_event = Event(
        "Battle of the Burger 2018",
        "Time Out New York's Battle of the Burger 2018\n" \
        "Battle is back and set to sizzle in 2018. Join us by the water " \
        "at LIC Landing for a summer cookout of epic proportions. Your " \
        "Instagram shots will be framed by the Empire State Building on " \
        "one side and the Chrysler Building on the other, as you dig " \
        "into some of the city's most delicious burgers, washed down " \
        "with icy Budweiser." \
        "https://www.timeout.com/newyork/restaurants/time-out-new-yorks-battle-of-the-burger-2018",
        "2018-8-16",
        "17:30",
        "2018-8-16",
        "22:00",
        get_admin_id(),
        bbq.id
        )
    insert_event(new_event)

    #drinks events
    message = "create_events(): {}".format("lookup drinks activity")
    with db_session(message) as db:
        drinks = db.query(models.Activity) \
                   .filter_by(name="drinks") \
                   .one()

    #Coney Island events
    message = "create_events(): {}".format("lookup Coney Island activity")
    with db_session(message) as db:
        coney_island = db.query(models.Activity) \
                         .filter_by(name="Coney Island") \
                         .one()

    events.clear()
    for date in recurring_event(calendar_start='2018-6-22',
                                calendar_end='2018-8-31',
                                interval='1 week'):
        new_event = Event(
            "Coney Island Friday Night Fireworks",
            "Coney Island's Friday Night Firework Series are on and " \
            "popping once again for summer 2018! Light up your Friday " \
            "nights, by joining us for a FREE firework show, every " \
            "Friday (weather permitting) this summer, until August 31. " \
            "For the best viewing, visitors are welcomed anywhere in " \
            "the Amusement District down to the beach and boardwalk. " \
            "Brought to you by Alliance for Coney Island\n\n" \
            "Location: Between West 10th Street and West 15th Street " \
            "in Coney Island Beach & Boardwalk Brooklyn",
            date.event_date,
            "21:30",
            date.event_date,
            "22:00",
            get_admin_id(),
            coney_island.id
            )
        events.append(new_event)
    insert_event(events)

    #outdoors events
    message = "create_events(): {}".format("lookup outdoors activity")
    with db_session(message) as db:
        outdoors = db.query(models.Activity) \
                     .filter_by(name="outdoors") \
                     .one()

    #camping events
    message = "create_events(): {}".format("lookup camping activity")
    with db_session(message) as db:
        camping = db.query(models.Activity) \
                    .filter_by(name="camping") \
                    .one()

    new_event = Event(
        "Glamping on Governors Island",
        "A quick ferry ride from downtown Manhattan, this peaceful " \
        "oasis is nestled near the hills of historic Governors " \
        "Island. You'll be surrounded by sprawling green space " \
        "with unparalleled views of the Statue of Liberty across " \
        "the New York Harbor. It's a retreat unlike any other in " \
        "the world.\n\nhttps://www.collectiveretreats.com/retreat/" \
        "collective-governors-island/\n\n" \
        "Location: Collective Governors Island, NYC",
        "2018-8-3",
        "10:00",
        "2018-10-31",
        "16:15",
        get_admin_id(),
        camping.id
        )
    insert_event(new_event)

    #boating events
    message = "create_events(): {}".format("lookup boating activity")
    with db_session(message) as db:
        boating = db.query(models.Activity) \
                    .filter_by(name="boating") \
                    .one()

    events.clear()
    for date in recurring_event(calendar_start='2018-5-31',
                                calendar_end='2018-9-30',
                                interval='1 week'):
        new_event = Event(
            "Kayaking",
            "Glide along the water while kayaking with the Brooklyn " \
            "Bridge Park Boathouse at the Pier 2 floating dock! Children " \
            "under 18 must have an adult guardian present. All levels " \
            "are welcome and no experience is necessary.\n\n" \
            "https://www.brooklynbridgepark.org/events/kayaking\n\n" \
            "Location: Brooklyn Bridge Park: Pier 2",
            date.event_date,
            "17:30",
            date.event_date,
            "18:45",
            get_admin_id(),
            boating.id
            )
        events.append(new_event)
    insert_event(events)

    events.clear()
    for date in recurring_event(calendar_start='2018-6-2',
                                calendar_end='2018-9-30',
                                interval='1 week'):
        new_event = Event(
            "Kayaking",
            "Glide along the water while kayaking with the Brooklyn " \
            "Bridge Park Boathouse at the Pier 2 floating dock! Children " \
            "under 18 must have an adult guardian present. All levels " \
            "are welcome and no experience is necessary.\n\n" \
            "https://www.brooklynbridgepark.org/events/kayaking\n\n" \
            "Location: Brooklyn Bridge Park: Pier 2",
            date.event_date,
            "10:00",
            date.event_date,
            "14:00",
            get_admin_id(),
            boating.id
            )
        events.append(new_event)
    insert_event(events)

    events.clear()
    for date in recurring_event(calendar_start='2018-6-3',
                                calendar_end='2018-9-30',
                                interval='1 week'):
        new_event = Event(
            "Kayaking",
            "Glide along the water while kayaking with the Brooklyn " \
            "Bridge Park Boathouse at the Pier 2 floating dock! Children " \
            "under 18 must have an adult guardian present. All levels " \
            "are welcome and no experience is necessary.\n\n" \
            "https://www.brooklynbridgepark.org/events/kayaking\n\n" \
            "Location: Brooklyn Bridge Park: Pier 2",
            date.event_date,
            "10:00",
            date.event_date,
            "14:00",
            get_admin_id(),
            boating.id
            )
        events.append(new_event)
    insert_event(events)

    #arts & film events
    message = "create_events(): {}".format("lookup arts & film activity")
    with db_session(message) as db:
        arts_and_film = db.query(models.Activity) \
                          .filter_by(name="arts & film") \
                          .one()

    new_event = Event(
        "Fantastic Mr. Fox",
        "SummerScreen Movie Series: " \
        "SummerScreen is Brooklyn's longest running film and music " \
        "series. Now in its 13th year, SummerScreen brings crowds to " \
        "Williamsburg's McCarren Park on Wednesdays in July and August " \
        "to enjoy a lineup of cult classic movies, live music, and " \
        "food and drink from local vendors.\n\n" \
        "You can bring: blankets, chairs, snacks, dogs, debit " \
        "card / cash\n\nhttps://www.nycgovparks.org/events/2018/08/08/" \
        "summerscreen-movie-series-fantastic-mr-fox",
        "2018-8-8",
        "18:00",
        "2018-8-8",
        "22:30",
        get_admin_id(),
        arts_and_film.id
        )
    insert_event(new_event)

    new_event = Event(
        "Die Hard",
        "SummerScreen Movie Series: " \
        "SummerScreen is Brooklyn's longest running film and music " \
        "series. Now in its 13th year, SummerScreen brings crowds to " \
        "Williamsburg's McCarren Park on Wednesdays in July and August " \
        "to enjoy a lineup of cult classic movies, live music, and " \
        "food and drink from local vendors.\n\n" \
        "You can bring: blankets, chairs, snacks, dogs, debit " \
        "card / cash\n\nhttps://www.nycgovparks.org/events/2018/08/15/" \
        "summerscreen-movie-series-die-hard",
        "2018-8-15",
        "18:00",
        "2018-8-15",
        "22:30",
        get_admin_id(),
        arts_and_film.id
        )
    insert_event(new_event)

    new_event = Event(
        "This is the Spinal Tap",
        "SummerScreen Movie Series: " \
        "SummerScreen is Brooklyn's longest running film and music " \
        "series. Now in its 13th year, SummerScreen brings crowds to " \
        "Williamsburg's McCarren Park on Wednesdays in July and August " \
        "to enjoy a lineup of cult classic movies, live music, and " \
        "food and drink from local vendors.\n\n" \
        "You can bring: blankets, chairs, snacks, dogs, debit " \
        "card / cash\n\nhttps://www.nycgovparks.org/events/2018/08/22/" \
        "summerscreen-movie-series",
        "2018-8-22",
        "18:00",
        "2018-8-22",
        "22:30",
        get_admin_id(),
        arts_and_film.id
        )
    insert_event(new_event)

    new_event = Event(
        "Audience Choice",
        "SummerScreen Movie Series: " \
        "SummerScreen is Brooklyn's longest running film and music " \
        "series. Now in its 13th year, SummerScreen brings crowds to " \
        "Williamsburg's McCarren Park on Wednesdays in July and August " \
        "to enjoy a lineup of cult classic movies, live music, and " \
        "food and drink from local vendors.\n\n" \
        "You can bring: blankets, chairs, snacks, dogs, debit " \
        "card / cash\n\nhttps://www.nycgovparks.org/events/2018/08/29/" \
        "summerscreen-movie-series",
        "2018-8-29",
        "18:00",
        "2018-8-29",
        "22:30",
        get_admin_id(),
        arts_and_film.id
        )
    insert_event(new_event)


def initialize_db():
    """setup events.db database with test records"""
    print("initialize_db() -> create_admin()")
    create_admin()

    print("initialize_db() -> create_activities()")
    create_activities()

    print("initialize_db() -> create_events()")
    create_events()


def print_activities():
    """print activity table records"""
    message = "print_activities()"
    with db_session(message) as db:
        activities = db.query(models.Activity) \
                       .all()

    print('\nActivities: ')
    for activity in activities:
        print(activity.name.title())


def print_events():
    """print event table records"""
    message = "print_events()"
    with db_session(message) as db:
        events = db.query(models.Event).all()

    print('\nEvents: ')
    for event in events:
        message = "print_events(): {}".format(event)
        with db_session(message) as db:
            activity = db.query(models.Activity) \
                         .filter_by(id=event.activity_id) \
                         .one()
        print('{} -> {}:\n          {}\n          start: {} {}' +
              '\n          end:   {} {}'.format(activity.name.title(),
                                                event.name,
                                                event.description,
                                                event.start_date,
                                                event.start_time,
                                                event.end_date,
                                                event.end_time))


def print_db():
    """print database records"""
    print_activities()
    print_events()


def main():
    """populate events database with test data"""
    initialize_db()
    #print_db()


if __name__ == '__main__':
    main()
