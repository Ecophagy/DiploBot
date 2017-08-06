from sqlalchemy import Column, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum

Base = declarative_base()
Database_Location = 'sqlite:///Diplomacy_moves.db'

class Movelist(Base):
    __tablename__ = 'movelist'
    discord_id = Column(String(50), primary_key=True)
    country = Column(String(50), nullable=False)
    playername = Column(String(250), nullable=False)
    moveset = Column(String(400), nullable=True)
    eliminated = Column(Boolean, default=False)


class Country(Enum):
    Austria = 1
    England = 2
    France = 3
    Germany = 4
    Italy = 5
    Russia = 6
    Turkey = 7
