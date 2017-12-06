import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm
import sys


DB = 'postgresql:///events.db'
declarative_base = sqlalchemy.ext.declarative.declarative_base()


class Activity(declarative_base):
    """Activity object

    An Activity represents a description used to categorize one or more Events.

    Attributes:
        id: Integer primary key for the Activity record.
        name: The name of the Activity.

    Dependencies:
        sqlalchemy.Column
        sqlalchemy.ext.declarative.declarative_base
        sqlalchemy.Integer
        sqlalchemy.String
    """
    __tablename__ = 'activity'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String(250), nullable=False)


class Event(declarative_base):
    """Event object

    An Event represents a planned occassion. Each Event is associated with the
    Activity which best represents it.

    Attributes:
        id: Integer primary key for the Event record.
        name: The name of the event.
        description: The description of the event.
        start_date: The date the event starts.
        _start_time: The time the event starts.
        end_date: The date the event ends.
        _end_time: The time the event ends.
        activity_id: The id for the Activity record associated with this event.

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
    activity_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('activity.id'))
    activity = sqlalchemy.orm.relationship(Activity)

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
