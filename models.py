import sys

from sqlalchemy import create_engine
from sqlalchemy import Column, ForeignKey, Integer, String
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
    activity_id = Column(Integer, ForeignKey('activity.id'))
    activity = relationship(Activity)


engine = create_engine('postgresql:///events.db')
Base.metadata.create_all(engine)
