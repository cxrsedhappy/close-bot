import enum
import datetime
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase


"""TODO: Fix warning "SAWarning: Object of type <PlayerClose> not in session"""


class Teams(enum.Enum):
    team1: int = 1
    team2: int = 2


class PlayerClose(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'PlayerCloseA'
    player_id = Column('player_id', ForeignKey("PlayersT.id"), primary_key=True)
    close_id = Column('close_id', ForeignKey("ClosesT.id"), primary_key=True)
    team = Column(Enum(Teams))
    close = relationship("Close", back_populates="players")
    player = relationship("Player", back_populates="closes")

    def __init__(self, team):
        self.team = team

    def __repr__(self):
        return f'<PlayerCloseA: {self.player_id}-{self.close_id}-{self.team}'


class Player(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'PlayersT'
    id = Column(Integer, primary_key=True)
    coins = Column(Integer, nullable=True)
    closes = relationship("PlayerClose", back_populates="player")

    def __init__(self, uid, coins=0):
        self.id = uid
        self.coins = coins

    def __repr__(self):
        return f'<Player: {self.id}>'


class Close(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'ClosesT'
    id = Column(Integer, primary_key=True, autoincrement=True)
    winner = Column(Enum(Teams))
    players = relationship("PlayerClose", back_populates="close")
    timestamp = Column(DateTime)

    def __init__(self, winner, timestamp=datetime.datetime.now()):
        self.winner = winner
        self.timestamp = timestamp

    def __repr__(self):
        return f'<Close: {self.id}, {self.winner} at {self.timestamp}>'
