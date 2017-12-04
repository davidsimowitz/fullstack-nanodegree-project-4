import sys

from sqlalchemy import create_engine
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy import Date, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

DB = 'postgresql:///events.db'

Base = declarative_base()


class Activity(Base):
    """Activity object

    An Activity represents a description used to categorize one or more Events.

    Attributes:
        id: Integer primary key for the Activity record.
        name: The name of the Activity.

    Dependencies:
        Base
        sqlalchemy.Column
        sqlalchemy.Integer
        sqlalchemy.String
    """
    __tablename__ = 'activity'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)


class Event(Base):
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
        Base
        sqlalchemy.Column
        sqlalchemy.Date
        sqlalchemy.ForeignKey
        sqlalchemy.Integer
        sqlalchemy.orm.relationship
        sqlalchemy.String
        sqlalchemy.Time
    """
    __tablename__ = 'event'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    description = Column(String(250))
    start_date = Column(Date)
    _start_time = Column(Time)
    end_date = Column(Date)
    _end_time = Column(Time)
    activity_id = Column(Integer, ForeignKey('activity.id'))
    activity = relationship(Activity)

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


engine = create_engine(DB)
Base.metadata.create_all(engine)
