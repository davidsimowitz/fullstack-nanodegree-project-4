import sys

from sqlalchemy import create_engine
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy import Date, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

DB = 'postgresql:///events.db'

Base = declarative_base()


class Activity(Base):
    """Activity Table"""
    __tablename__ = 'activity'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)


class Event(Base):
    """Event Table"""
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
        start_time = str(self._start_time)
        return start_time[:5]

    @start_time.setter
    def start_time(self, start_time):
        self._start_time = start_time

    @property
    def end_time(self):
        end_time = str(self._end_time)
        return end_time[:5]

    @end_time.setter
    def end_time(self, end_time):
        self._end_time = end_time


engine = create_engine(DB)
Base.metadata.create_all(engine)
