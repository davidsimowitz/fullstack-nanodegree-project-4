import datetime
import os
import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm
import sys

# Update correct user for database access.
DB = 'postgresql://<user>:<password>@<host>:<port>/events.db'
declarative_base = sqlalchemy.ext.declarative.declarative_base()


def icon_list(path='/var/www/flask/coordinate/static/img/'):
    """returns a list of icon urls

    Args:
        path: relative directory to be searched

    Returns:
        icons: A list containing the relative urls of icon
               svg files located in the supplied path.

    Dependencies:
        os.walk
    """
    icons = []
    for root, _, images in os.walk(path):
        for image in images:
            if image.endswith('-icon.svg'):
                icons.append('/static/img/' + image)
    return icons


class UserAccount(declarative_base):
    """User account object

    Represents a user login account to create/modify events.

    Attributes:
        id: Integer primary key for the user account record.
        name: The name of the user.
        email: The primary email of the user.
        picture: An image associated with the user account.

    Dependencies:
        sqlalchemy.Column
        sqlalchemy.ext.declarative.declarative_base
        sqlalchemy.Integer
    """
    __tablename__ = 'user_account'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
    email = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
    picture = sqlalchemy.Column(sqlalchemy.String(250))


class Activity(declarative_base):
    """Activity object

    An activity represents a description used to categorize one or more events.

    Attributes:
        id: Integer primary key for the activity record.
        name: The name of the activity.
        icon: The icon for the activity stored as a URL.
        user_id: The id for the user account record associated with
            this activity.

    Dependencies:
        sqlalchemy.Column
        sqlalchemy.ext.declarative.declarative_base
        sqlalchemy.Integer
        sqlalchemy.String
    """
    __tablename__ = 'activity'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
    icon = sqlalchemy.Column(sqlalchemy.String(250), nullable=False)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey('user_account.id'))
    user_account = sqlalchemy.orm.relationship(UserAccount)

    @property
    def serialize(self):
        """Return Activity record in a serializable format"""
        return {
                'name': self.name,
                'icon': self.icon,
                'id': self.id,
               }


class Event(declarative_base):
    """Event object

    An event represents a planned occassion. Each event is associated with the
    activity which best represents it.

    Attributes:
        id: Integer primary key for the event record.
        name: The name of the event.
        description: The description of the event.
        start_date: The date the event starts.
        _start_time: The time the event starts.
        end_date: The date the event ends.
        _end_time: The time the event ends.
        user_id: The id for the user account record associated with this event.
        activity_id: The id for the activity record associated with this event.

    Dependencies:
        sqlalchemy.Column
        sqlalchemy.Date
        sqlalchemy.ext.declarative.declarative_base
        sqlalchemy.ForeignKey
        sqlalchemy.Integer
        sqlalchemy.orm.relationship
        sqlalchemy.String
        sqlalchemy.Time
    """
    __tablename__ = 'event'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String(1000))
    start_date = sqlalchemy.Column(sqlalchemy.Date, nullable=False)
    _start_time = sqlalchemy.Column(sqlalchemy.Time)
    end_date = sqlalchemy.Column(sqlalchemy.Date, nullable=False)
    _end_time = sqlalchemy.Column(sqlalchemy.Time)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey('user_account.id'))
    user_account = sqlalchemy.orm.relationship(UserAccount)
    activity_id = sqlalchemy.Column(sqlalchemy.Integer,
                                    sqlalchemy.ForeignKey('activity.id'))
    activity = sqlalchemy.orm.relationship(Activity)

    @property
    def serialize(self):
        """Return Event record in a serializable format"""
        return {
                'name': self.name,
                'id': self.id,
                'description': self.description,
                'start date': str(self.start_date),
                'start time': self.start_time,
                'end date': str(self.end_date),
                'end time': self.end_time,
               }

    @property
    def start_time(self):
        """Return start time in <HH:MM> format"""
        return str(self._start_time)[:5]

    @start_time.setter
    def start_time(self, start_time):
        """Set start time"""
        self._start_time = start_time

    @property
    def end_time(self):
        """Return end time in <HH:MM> format"""
        return str(self._end_time)[:5]

    @end_time.setter
    def end_time(self, end_time):
        """Set end time"""
        self._end_time = end_time


class Hosting(declarative_base):
    """Hosting object

    A hosting object represents a relationship between a user and
    an event they are hosting.

    Attributes:
        user_id: The id for the user hosting the associated event.
        event_id: The id for the event being hosted by the associated user.

    Dependencies:
        sqlalchemy.Column
        sqlalchemy.ext.declarative.declarative_base
        sqlalchemy.ForeignKey
        sqlalchemy.Integer
        sqlalchemy.orm.relationship
    """
    __tablename__ = 'hosting'

    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey('user_account.id'),
                                primary_key=True)
    event_id = sqlalchemy.Column(sqlalchemy.Integer,
                                 sqlalchemy.ForeignKey('event.id'),
                                 primary_key=True)
    user_account = sqlalchemy.orm.relationship(UserAccount)
    event = sqlalchemy.orm.relationship(Event)


class Attending(declarative_base):
    """Attending object

    An attending object represents a relationship between a user and
    an event they are attending.

    Attributes:
        user_id: The id for the user attending the associated event.
        event_id: The id for the event being attended by the associated user.

    Dependencies:
        sqlalchemy.Column
        sqlalchemy.ext.declarative.declarative_base
        sqlalchemy.ForeignKey
        sqlalchemy.Integer
        sqlalchemy.orm.relationship
    """
    __tablename__ = 'attending'

    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey('user_account.id'),
                                primary_key=True)
    event_id = sqlalchemy.Column(sqlalchemy.Integer,
                                 sqlalchemy.ForeignKey('event.id'),
                                 primary_key=True)
    user_account = sqlalchemy.orm.relationship(UserAccount)
    event = sqlalchemy.orm.relationship(Event)


class Considering(declarative_base):
    """Attending object

    A considering object represents a relationship between a user and
    an event they are considering to attend.

    Attributes:
        user_id: The id for the user considering the associated event.
        event_id: The id for the event being considered by the associated user.

    Dependencies:
        sqlalchemy.Column
        sqlalchemy.ext.declarative.declarative_base
        sqlalchemy.ForeignKey
        sqlalchemy.Integer
        sqlalchemy.orm.relationship
    """
    __tablename__ = 'considering'

    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey('user_account.id'),
                                primary_key=True)
    event_id = sqlalchemy.Column(sqlalchemy.Integer,
                                 sqlalchemy.ForeignKey('event.id'),
                                 primary_key=True)
    user_account = sqlalchemy.orm.relationship(UserAccount)
    event = sqlalchemy.orm.relationship(Event)


engine = sqlalchemy.create_engine(DB)
declarative_base.metadata.create_all(engine)
