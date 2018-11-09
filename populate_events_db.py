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
                     "https://lh6.googleusercontent.com/-bO6Jr_RkpXw"
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
    message = "get_admin_id()"
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
                       "movies",
                       "/static/img/popcorn-and-soda-icon.svg",
                       user_id
                       )
    activities.append(new_activity)

    new_activity = Activity(
                       "outdoors",
                       "/static/img/tree-icon.svg",
                       user_id
                       )
    activities.append(new_activity)

    new_activity = Activity(
                       "running",
                       "/static/img/sun-icon.svg",
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
                       "BBQ",
                       "/static/img/burger-icon.svg",
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
        def insert(event, message):
            with db_session(message) as db:
                if event.start_time and event.end_time:
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
                elif event.start_time:
                    new_event = models.Event(
                                       name=event.name,
                                       description=event.description,
                                       start_date=event.start_date,
                                       _start_time=event.start_time,
                                       end_date=event.end_date,
                                       user_id=event.user_id,
                                       activity_id=event.activity_id
                                       )
                elif event.end_time:
                    new_event = models.Event(
                                       name=event.name,
                                       description=event.description,
                                       start_date=event.start_date,
                                       end_date=event.end_date,
                                       _end_time=event.end_time,
                                       user_id=event.user_id,
                                       activity_id=event.activity_id
                                       )
                else:
                    new_event = models.Event(
                                       name=event.name,
                                       description=event.description,
                                       start_date=event.start_date,
                                       end_date=event.end_date,
                                       user_id=event.user_id,
                                       activity_id=event.activity_id
                                       )
                db.add(new_event)
                db.commit()

        if isinstance(event_record, tuple):
            message = "create_events(): {}".format(event_record)
            insert(event_record, message)
        else:
            for event in event_record:
                message = "create_events(): {}".format(event)
                insert(event, message)

    # swimming events
    message = "create_events(): {}".format("lookup swimming activity")
    with db_session(message) as db:
        swimming = db.query(models.Activity) \
                     .filter_by(name="swimming") \
                     .one()

    # Brooklyn Bridge Park: Pop-Up Pool
    events.clear()
    for date in recurring_event(calendar_start='2019-8-5',
                                calendar_end='2019-8-18'):
        new_event = Event(
            name="Pop-Up Pool",
            description="Take a dip in one of New York City's coolest hidden "
            "gems, then relax on the beach after your swim. "
            "(Brooklyn Bridge Park: Pier 2)",
            start_date=date.event_date,
            start_time="10:00",
            end_date=date.event_date,
            end_time="10:45",
            user_id=get_admin_id(),
            activity_id=swimming.id
            )
        print(new_event)
        events.append(new_event)
    print(events)
    insert_event(events)

    events.clear()
    for date in recurring_event(calendar_start='2019-8-5',
                                calendar_end='2019-8-18'):
        new_event = Event(
            name="Pop-Up Pool",
            description="Take a dip in one of New York City's coolest hidden "
            "gems, then relax on the beach after your swim. "
            "(Brooklyn Bridge Park: Pier 2)",
            start_date=date.event_date,
            start_time="11:00",
            end_date=date.event_date,
            end_time="11:45",
            user_id=get_admin_id(),
            activity_id=swimming.id
            )
        print(new_event)
        events.append(new_event)
    print(events)
    insert_event(events)

    events.clear()
    for date in recurring_event(calendar_start='2019-8-5',
                                calendar_end='2019-8-18'):
        new_event = Event(
            name="Pop-Up Pool",
            description="Take a dip in one of New York City's coolest hidden "
            "gems, then relax on the beach after your swim. "
            "(Brooklyn Bridge Park: Pier 2)",
            start_date=date.event_date,
            start_time="12:00",
            end_date=date.event_date,
            end_time="12:45",
            user_id=get_admin_id(),
            activity_id=swimming.id
            )
        print(new_event)
        events.append(new_event)
    print(events)
    insert_event(events)

    events.clear()
    for date in recurring_event(calendar_start='2019-8-5',
                                calendar_end='2019-8-18'):
        new_event = Event(
            name="Pop-Up Pool",
            description="Take a dip in one of New York City's coolest hidden "
            "gems, then relax on the beach after your swim. "
            "(Brooklyn Bridge Park: Pier 2)",
            start_date=date.event_date,
            start_time="13:00",
            end_date=date.event_date,
            end_time="13:45",
            user_id=get_admin_id(),
            activity_id=swimming.id
            )
        print(new_event)
        events.append(new_event)
    print(events)
    insert_event(events)

    events.clear()
    for date in recurring_event(calendar_start='2019-8-5',
                                calendar_end='2019-8-18'):
        new_event = Event(
            name="Pop-Up Pool",
            description="Take a dip in one of New York City's coolest hidden "
            "gems, then relax on the beach after your swim. "
            "(Brooklyn Bridge Park: Pier 2)",
            start_date=date.event_date,
            start_time="14:00",
            end_date=date.event_date,
            end_time="14:45",
            user_id=get_admin_id(),
            activity_id=swimming.id
            )
        print(new_event)
        events.append(new_event)
    print(events)
    insert_event(events)

    events.clear()
    for date in recurring_event(calendar_start='2019-8-5',
                                calendar_end='2019-8-18'):
        new_event = Event(
            name="Pop-Up Pool",
            description="Take a dip in one of New York City's coolest hidden "
            "gems, then relax on the beach after your swim. "
            "(Brooklyn Bridge Park: Pier 2)",
            start_date=date.event_date,
            start_time="15:00",
            end_date=date.event_date,
            end_time="15:45",
            user_id=get_admin_id(),
            activity_id=swimming.id
            )
        print(new_event)
        events.append(new_event)
    print(events)
    insert_event(events)

    # movies events
    message = "create_events(): {}".format("lookup movies activity")
    with db_session(message) as db:
        movies = db.query(models.Activity) \
                   .filter_by(name="movies") \
                   .one()

    new_event = Event(
        name="BlacKkKlansman (premier)",
        description="From visionary filmmaker Spike Lee comes the "
        "incredible true story of an American hero. It's the early "
        "1970s, and Ron Stallworth (John David Washington) is the first "
        "African-American detective to serve in the Colorado Springs "
        "Police Department. Determined to make a name for himself, "
        "Stallworth bravely sets out on a dangerous mission: infiltrate "
        "and expose the Ku Klux Klan. The young detective soon recruits a "
        "more seasoned colleague, Flip Zimmerman (Adam Driver), into the "
        "undercover investigation of a lifetime. Together, they team up to "
        "take down the extremist hate group as the organization aims to "
        "sanitize its violent rhetoric to appeal to the mainstream. "
        "Produced by the team behind the Academy-Award® winning Get Out.",
        start_date="2019-8-9",
        start_time="19:00",
        end_date="2019-8-9",
        end_time=None,
        user_id=get_admin_id(),
        activity_id=movies.id
        )
    insert_event(new_event)

    # music events
    message = "create_events(): {}".format("lookup music activity")
    with db_session(message) as db:
        music = db.query(models.Activity) \
                  .filter_by(name="music") \
                  .one()
    # Bargemusic events
    events.clear()
    for date in recurring_event(calendar_start="2019-8-3",
                                calendar_end="2019-8-18",
                                interval="1 week"):
        new_event = Event(
            name="Bargemusic",
            description="Bargemusic Presents Admission FREE Concerts, "
            "the 'Music in Motion' Series - a one hour performance (no "
            "intermission), including a Q & A session with the musicians. "
            "Doors open 15 minutes before the performance - no "
            "reserved seating is available. Visit bargemusic.org for more!",
            start_date=date.event_date,
            start_time="16:00",
            end_date=date.event_date,
            end_time="17:00",
            user_id=get_admin_id(),
            activity_id=music.id
            )
        events.append(new_event)
    insert_event(events)

    # outdoors events
    message = "create_events(): {}".format("lookup hiking activity")
    with db_session(message) as db:
        outdoors = db.query(models.Activity) \
                   .filter_by(name="outdoors") \
                   .one()

    # Farmer's Market
    events.clear()
    for date in recurring_event(calendar_start="2019-8-3",
                                calendar_end="2019-8-31",
                                interval='1 week'):
        new_event = Event(
            name="Farmer's Market",
            description="Join the Wyckoff farm team as we share our "
            "harvest with the community. Stop by and grab your veggies, "
            "fruits, herbs, seeds, and local crafts at affordable "
            "prices. Make a day of it and check out other events that "
            "may be happening that day, including workshops, family "
            "day, or hands-on skill building. "
            "(Fidler-Wyckoff House Park, Brooklyn)",
            start_date=date.event_date,
            start_time="11:00",
            end_date=date.event_date,
            end_time="15:00",
            user_id=get_admin_id(),
            activity_id=outdoors.id
            )
        events.append(new_event)
    insert_event(events)

    # Beach Walk
    events.clear()
    for date in recurring_event(calendar_start="2019-7-31",
                                calendar_end="2019-8-31",
                                interval='1 week'):
        new_event = Event(
            name="Beach Walk",
            description="Explore the shore! Enjoy an interpretive walk"
            "at Conference House Park's Joline Avenue beach. Beachcomb "
            "along one of Staten Island's most diverse natural shorelines. "
            "The walk starts at the corner of Hylan Boulevard and Joline "
            "Avenue (Staten Island).",
            start_date=date.event_date,
            start_time="15:00",
            end_date=date.event_date,
            end_time="16:00",
            user_id=get_admin_id(),
            activity_id=outdoors.id
            )
        events.append(new_event)
    insert_event(events)

    # Brooklyn Bridge Park - Green Team
    events.clear()
    for date in recurring_event(calendar_start="2019-8-3",
                                calendar_end="2019-8-31",
                                interval='1 week'):
        new_event = Event(
            name="Green Team",
            description="The Green Team provides essential horticultural "
            "care to the Park, including planting, mulching, and removing "
            "invasive plants. The Green Team is a wonderful opportunity "
            "to learn about gardening, enjoy nature, and make the Park "
            "look its best. Join this dedicated corps of volunteers who "
            "beautify the Park every week! (Brooklyn Bridge Park - Pier 1)",
            start_date=date.event_date,
            start_time="10:00",
            end_date=date.event_date,
            end_time="12:00",
            user_id=get_admin_id(),
            activity_id=outdoors.id
            )
        events.append(new_event)
    insert_event(events)

    # Brooklyn Bridge Park - Green Team
    events.clear()
    for date in recurring_event(calendar_start="2019-8-1",
                                calendar_end="2019-8-31",
                                interval='1 week'):
        new_event = Event(
            name="Smorgasburg at the Movies",
            description="Enjoy sweet treats, savory snacks, and "
            "drinks from Smorgasburg during Movies With A View!"
            "Leave the picnic baskets at home and enjoy food and "
            "drink from Smorgasburg. Enjoy cheeseburgers from Burger "
            "Supreme, crab cakes from Musser's Famous Crab Cake "
            "Sandwiches, Belgian-cut fries and fried chicken sandwiches "
            "from Home Frite, pizza by Wood Fired Edibles, and homemade "
            "ice cream from Bona Bona Ice Cream. "
            "(Brooklyn Bridge Park - Granite Prospect)",
            start_date=date.event_date,
            start_time="18:00",
            end_date=date.event_date,
            end_time=None,
            user_id=get_admin_id(),
            activity_id=outdoors.id
            )
        events.append(new_event)
    insert_event(events)

    # Brooklyn Bridge Park - Waterfront Workouts Zumba
    events.clear()
    for date in recurring_event(calendar_start="2019-8-4",
                                calendar_end="2019-8-31",
                                interval='1 week'):
        new_event = Event(
            name="Waterfront Workouts",
            description="Dodge YMCA fitness instructor Alma Bonilla's "
            "Zumba classes are so much fun you'll forget that you're "
            "burning calories. ZUMBA is a fusion of Latin and "
            "International music, utilizing dance themes that create "
            "a dynamic, exciting, effective fitness program. The "
            "routines feature aerobic training with a combination of "
            "fast and slow rhythms that tone and sculpt the body."
            "(Brooklyn Bridge Park - Bocce Courts)",
            start_date=date.event_date,
            start_time="16:00",
            end_date=date.event_date,
            end_time=None,
            user_id=get_admin_id(),
            activity_id=outdoors.id
            )
        events.append(new_event)
    insert_event(events)

    # BBQ events
    message = "create_events(): {}".format("lookup BBQ activity")
    with db_session(message) as db:
        bbq = db.query(models.Activity) \
                .filter_by(name="BBQ") \
                .one()

    new_event = Event(
        name="Battle of the Burger 2019",
        description="Time Out New York's Battle of the Burger 2019 "
        "Battle is back and set to sizzle in 2019. Join us by the water "
        "at LIC Landing for a summer cookout of epic proportions. Your "
        "Instagram shots will be framed by the Empire State Building on "
        "one side and the Chrysler Building on the other, as you dig "
        "into some of the city's most delicious burgers, washed down "
        "with icy Budweiser.",
        start_date="2019-8-15",
        start_time="17:30",
        end_date="2019-8-15",
        end_time="22:00",
        user_id=get_admin_id(),
        activity_id=bbq.id
        )
    insert_event(new_event)

    # running events
    message = "create_events(): {}".format("lookup outdoors activity")
    with db_session(message) as db:
        running = db.query(models.Activity) \
                     .filter_by(name="running") \
                     .one()

    # NYRR: Turnover Tuesdays
    events.clear()
    for date in recurring_event(calendar_start="2019-8-6",
                                calendar_end="2019-8-31",
                                interval='1 week'):
        new_event = Event(
            name="NYRR: Turnover Tuesdays",
            description="Turnover Tuesdays, which focus on interval "
            "training (faster short runs with rest intervals between "
            "them). Meet at NYRR RUNCENTER featuring the New Balance "
            "Run Hub. (Manhattan - Central Park)",
            start_date=date.event_date,
            start_time="6:30",
            end_date=date.event_date,
            end_time=None,
            user_id=get_admin_id(),
            activity_id=running.id
            )
        events.append(new_event)
    insert_event(events)

    events.clear()
    for date in recurring_event(calendar_start="2019-8-6",
                                calendar_end="2019-8-31",
                                interval='1 week'):
        new_event = Event(
            name="NYRR: Turnover Tuesdays",
            description="Turnover Tuesdays, which focus on interval "
            "training (faster short runs with rest intervals between "
            "them). Meet at Grand Army Plaza entrance to Prospect Park. "
            "(Brooklyn - Prospect Park)",
            start_date=date.event_date,
            start_time="6:30",
            end_date=date.event_date,
            end_time=None,
            user_id=get_admin_id(),
            activity_id=running.id
            )
        events.append(new_event)
    insert_event(events)

    events.clear()
    for date in recurring_event(calendar_start="2019-8-6",
                                calendar_end="2019-8-31",
                                interval='1 week'):
        new_event = Event(
            name="NYRR: Turnover Tuesdays",
            description="Turnover Tuesdays, which focus on interval "
            "training (faster short runs with rest intervals between "
            "them). Meet at NYRR RUNCENTER featuring the New Balance "
            "Run Hub. (Manhattan - Central Park)",
            start_date=date.event_date,
            start_time="18:30",
            end_date=date.event_date,
            end_time=None,
            user_id=get_admin_id(),
            activity_id=running.id
            )
        events.append(new_event)
    insert_event(events)

    events.clear()
    for date in recurring_event(calendar_start="2019-8-6",
                                calendar_end="2019-8-31",
                                interval='1 week'):
        new_event = Event(
            name="NYRR: Turnover Tuesdays",
            description="Turnover Tuesdays, which focus on interval "
            "training (faster short runs with rest intervals between "
            "them). Meet at Grand Army Plaza entrance to Prospect Park. "
            "(Brooklyn - Prospect Park)",
            start_date=date.event_date,
            start_time="18:30",
            end_date=date.event_date,
            end_time=None,
            user_id=get_admin_id(),
            activity_id=running.id
            )
        events.append(new_event)
    insert_event(events)

    # NYRR: Mashup Wednesdays
    events.clear()
    for date in recurring_event(calendar_start="2019-8-7",
                                calendar_end="2019-8-31",
                                interval='1 week'):
        new_event = Event(
            name="NYRR: Mashup Wednesdays",
            description="Mashup Wednesdays, which offer a variety of "
            "interval and tempo workouts. Meet at NYRR RUNCENTER featuring "
            "the New Balance Run Hub. (Manhattan - Central Park)",
            start_date=date.event_date,
            start_time="9:30",
            end_date=date.event_date,
            end_time=None,
            user_id=get_admin_id(),
            activity_id=running.id
            )
        events.append(new_event)
    insert_event(events)

    events.clear()
    for date in recurring_event(calendar_start="2019-8-7",
                                calendar_end="2019-8-31",
                                interval='1 week'):
        new_event = Event(
            name="NYRR: Mashup Wednesdays",
            description="Mashup Wednesdays, which offer a variety of "
            "interval and tempo workouts. Meet at the benches next to "
            "the handball court. (Bronx - Van Cortlandt Park)",
            start_date=date.event_date,
            start_time="6:30",
            end_date=date.event_date,
            end_time=None,
            user_id=get_admin_id(),
            activity_id=running.id
            )
        events.append(new_event)
    insert_event(events)

    events.clear()
    for date in recurring_event(calendar_start="2019-8-7",
                                calendar_end="2019-8-31",
                                interval='1 week'):
        new_event = Event(
            name="NYRR: Mashup Wednesdays",
            description="Mashup Wednesdays, which offer a variety of "
            "interval and tempo workouts. Meet at the field house, "
            "between the track and the tennis courts. (Queens - Astoria Park)",
            start_date=date.event_date,
            start_time="6:30",
            end_date=date.event_date,
            end_time=None,
            user_id=get_admin_id(),
            activity_id=running.id
            )
        events.append(new_event)
    insert_event(events)

    events.clear()
    for date in recurring_event(calendar_start="2019-8-7",
                                calendar_end="2019-8-31",
                                interval='1 week'):
        new_event = Event(
            name="NYRR: Mashup Wednesdays",
            description="Mashup Wednesdays, which offer a variety of "
            "interval and tempo workouts. Meet at the field house, "
            "between the track and the tennis courts. (Queens - Astoria Park)",
            start_date=date.event_date,
            start_time="18:30",
            end_date=date.event_date,
            end_time=None,
            user_id=get_admin_id(),
            activity_id=running.id
            )
        events.append(new_event)
    insert_event(events)

    events.clear()
    for date in recurring_event(calendar_start="2019-8-7",
                                calendar_end="2019-8-31",
                                interval='1 week'):
        new_event = Event(
            name="NYRR: Mashup Wednesdays",
            description="Mashup Wednesdays, which offer a variety of "
            "interval and tempo workouts. Meet at Park Drive off of "
            "Clove Road. (Staten Island - Clove Lakes Park)",
            start_date=date.event_date,
            start_time="19:30",
            end_date=date.event_date,
            end_time=None,
            user_id=get_admin_id(),
            activity_id=running.id
            )
        events.append(new_event)
    insert_event(events)

    # NYRR: Winged-Foot Wednesdays
    events.clear()
    for date in recurring_event(calendar_start="2019-8-7",
                                calendar_end="2019-8-31",
                                interval='1 week'):
        new_event = Event(
            name="NYRR: Winged-Foot Wednesdays",
            description="Winged-Foot Wednesdays, which concentrate on "
            "speed intervals. Meet at East River Track entrance. "
            "(Manhattan - East River Track)",
            start_date=date.event_date,
            start_time="6:30",
            end_date=date.event_date,
            end_time=None,
            user_id=get_admin_id(),
            activity_id=running.id
            )
        events.append(new_event)
    insert_event(events)

    # NYRR: Tempo Thursdays
    events.clear()
    for date in recurring_event(calendar_start="2019-8-8",
                                calendar_end="2019-8-31",
                                interval='1 week'):
        new_event = Event(
            name="NYRR: Tempo Thursdays",
            description="Tempo Thursdays, which primarily feature tempo "
            "runs (steady runs at a challenging effort). Meet at NYRR "
            "RUNCENTER featuring the New Balance Run Hub. "
            "(Manhattan - Central Park)",
            start_date=date.event_date,
            start_time="6:30",
            end_date=date.event_date,
            end_time=None,
            user_id=get_admin_id(),
            activity_id=running.id
            )
        events.append(new_event)
    insert_event(events)

    events.clear()
    for date in recurring_event(calendar_start="2019-8-8",
                                calendar_end="2019-8-31",
                                interval='1 week'):
        new_event = Event(
            name="NYRR: Tempo Thursdays",
            description="Tempo Thursdays, which primarily feature tempo "
            "runs (steady runs at a challenging effort). Meet at Grand "
            "Army Plaza entrance to Prospect Park. (Brooklyn - Prospect Park)",
            start_date=date.event_date,
            start_time="6:30",
            end_date=date.event_date,
            end_time=None,
            user_id=get_admin_id(),
            activity_id=running.id
            )
        events.append(new_event)
    insert_event(events)

    events.clear()
    for date in recurring_event(calendar_start="2019-8-8",
                                calendar_end="2019-8-31",
                                interval='1 week'):
        new_event = Event(
            name="NYRR: Tempo Thursdays",
            description="Tempo Thursdays, which primarily feature tempo "
            "runs (steady runs at a challenging effort). Meet at NYRR "
            "RUNCENTER featuring the New Balance Run Hub. "
            "(Manhattan - Central Park)",
            start_date=date.event_date,
            start_time="18:30",
            end_date=date.event_date,
            end_time=None,
            user_id=get_admin_id(),
            activity_id=running.id
            )
        events.append(new_event)
    insert_event(events)

    events.clear()
    for date in recurring_event(calendar_start="2019-8-8",
                                calendar_end="2019-8-31",
                                interval='1 week'):
        new_event = Event(
            name="NYRR: Tempo Thursdays",
            description="Tempo Thursdays, which primarily feature tempo "
            "runs (steady runs at a challenging effort). Meet at Grand "
            "Army Plaza entrance to Prospect Park. (Brooklyn - Prospect Park)",
            start_date=date.event_date,
            start_time="18:30",
            end_date=date.event_date,
            end_time=None,
            user_id=get_admin_id(),
            activity_id=running.id
            )
        events.append(new_event)
    insert_event(events)

    # NYRR: Long Weekend Runs
    events.clear()
    for date in recurring_event(calendar_start="2019-8-10",
                                calendar_end="2019-8-31",
                                interval='1 week'):
        new_event = Event(
            name="NYRR: Weekend Long Runs",
            description="Coach-led runs on the streets of NYC in the "
            "weeks leading up to key NYRR races throughout the year. "
            "(NYC - Various locations)",
            start_date=date.event_date,
            start_time="7:00",
            end_date=date.event_date,
            end_time=None,
            user_id=get_admin_id(),
            activity_id=running.id
            )
        events.append(new_event)
    insert_event(events)


def initialize_db():
    """setup events.db database with test records"""
    print("initialize_db() -> create_admin()")
    create_admin()

    print("initialize_db() -> create_activities()")
    create_activities()

    print("initialize_db() -> create_events()")
    create_events()


def main():
    """populate events database with test data"""
    initialize_db()


if __name__ == '__main__':
    main()
