import datetime
import os
import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm
import sys


DB = 'postgresql:///events.db'
declarative_base = sqlalchemy.ext.declarative.declarative_base()

def icon_list(path='static/img/'):
    """returns a list of icon urls

    Args:
        path: relative directory to be searched

    Returns:
        icons: A list containing the relative urls of icon
               svg files located in the supplied path.

    Dependencies:
        os.walk
    """
    icons= []
    for root, _, images in os.walk(path):
        for image in images:
            if image.endswith('-icon.svg'):
                icons.append('/' + root + image)
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
    name = sqlalchemy.Column(sqlalchemy.String(250), nullable=False)
    email = sqlalchemy.Column(sqlalchemy.String(250), nullable=False)
    picture = sqlalchemy.Column(sqlalchemy.String(250))


class Activity(declarative_base):
    """Activity object

    An activity represents a description used to categorize one or more events.

    Attributes:
        id: Integer primary key for the activity record.
        name: The name of the activity.
        icon: The icon for the activity stored as a URL.
        user_id: The id for the user account record associated with this activity.

    Dependencies:
        sqlalchemy.Column
        sqlalchemy.ext.declarative.declarative_base
        sqlalchemy.Integer
        sqlalchemy.String
    """
    __tablename__ = 'activity'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String(250), nullable=False)
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
    name = sqlalchemy.Column(sqlalchemy.String(250), nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String(250))
    start_date = sqlalchemy.Column(sqlalchemy.Date)
    _start_time = sqlalchemy.Column(sqlalchemy.Time)
    end_date = sqlalchemy.Column(sqlalchemy.Date)
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
                'start date': self.start_date,
                'start time': self.start_time_12_hour_notation,
                'starting date long form': self.starting_date_long_form,
                'end date': self.end_date,
                'end time': self.end_time_12_hour_notation,
               }

    @property
    def starting_date_long_form(self):
        """Return starting date in <Day_of_the_week, Month DD, YYYY> format"""
        MONTH = ['January', 'February', 'March', 'April', 'May',
                 'June', 'July', 'August', 'September', 'October',
                 'November', 'December']
        DAY_OF_THE_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                           'Friday', 'Saturday', 'Sunday']
        return '{}, {} {}, {}'.format(
                 DAY_OF_THE_WEEK[self.start_date.weekday()],
                 MONTH[self.start_date.month - 1],
                 self.start_date.day,
                 self.start_date.year)

    @starting_date_long_form.setter
    def starting_date_long_form(self, starting_date):
        """Starting date in long form notation is read-only"""
        raise AttributeError('<starting_date_long_form> is read-only')

    @property
    def start_time(self):
        """Return start time in <HH:MM> format"""
        start_time = str(self._start_time)
        return start_time[:5]

    @start_time.setter
    def start_time(self, start_time):
        """Set start time"""
        self._start_time = start_time

    @property
    def end_time(self):
        """Return end time in <HH:MM> format"""
        end_time = str(self._end_time)
        return end_time[:5]

    @end_time.setter
    def end_time(self, end_time):
        """Set end time"""
        self._end_time = end_time

    @property
    def start_time_12_hour_notation(self):
        """Return the start time in <HH:MM AM/PM> format"""
        try:
            start_time = str(self._start_time)
            hour = int(start_time[:2])
        except:
            pass
        else:
            if hour > 11:
                hour = hour - 12 if hour > 12 else hour
                return '{}:{} PM'.format(hour, start_time[3:5])
            else:
                hour = 12 if hour is 0 else hour
                return '{}:{} AM'.format(hour, start_time[3:5])

    @start_time_12_hour_notation.setter
    def start_time_12_hour_notation(self, start_time):
        """12-hour-notation version of start time is read-only"""
        raise AttributeError('<start_time_12_hour_notation> is read-only')

    @property
    def end_time_12_hour_notation(self):
        """Return the end time in <HH:MM AM/PM> format"""
        try:
            end_time = str(self._end_time)
            hour = int(end_time[:2])
        except:
            pass
        else:
            if hour > 11:
                hour = hour - 12 if hour > 12 else hour
                return '{}:{} PM'.format(hour, end_time[3:5])
            else:
                hour = 12 if hour is 0 else hour
                return '{}:{} AM'.format(hour, end_time[3:5])

    @end_time_12_hour_notation.setter
    def end_time_12_hour_notation(self, end_time):
        """12-hour-notation version of end time is read-only"""
        raise AttributeError('<start_time_12_hour_notation> is read-only')


engine = sqlalchemy.create_engine(DB)
declarative_base.metadata.create_all(engine)
