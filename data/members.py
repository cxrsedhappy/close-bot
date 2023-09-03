import sqlalchemy

from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase

player_close = sqlalchemy.Table('player-close', SqlAlchemyBase.metadata,
                                Column('player_id', Integer, ForeignKey('player.id')),
                                Column('close_id', Integer, ForeignKey('close.id'))
                                )


class PlayerCloser(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'asdlayer'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coins = Column(Integer, nullable=True)

    def __repr__(self):
        return f'player<{self.id}>'


class Player(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'player'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coins = Column(Integer, nullable=True)

    def __repr__(self):
        return f'player<{self.id}>'


class Close(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'close'
    id = Column(Integer, primary_key=True, autoincrement=True)
    winner = Column(Boolean)
    timestamp = Column(DateTime)

    def __repr__(self):
        return f'close<{self.id}>'
