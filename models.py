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
    start_time = Column(Time)
    end_date = Column(Date)
    end_time = Column(Time)
    activity_id = Column(Integer, ForeignKey('activity.id'))
    activity = relationship(Activity)


engine = create_engine(DB)
Base.metadata.create_all(engine)
