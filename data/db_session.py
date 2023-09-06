import enum

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base


from sqlalchemy_serializer import SerializerMixin


class Teams(enum.Enum):
    team1: int = 1
    team2: int = 2


Base = declarative_base()
engine = create_async_engine('sqlite+aiosqlite:///db/database?check_same_thread=False', echo=False)
__session = async_sessionmaker(engine, expire_on_commit=False)


class Player(Base, SerializerMixin):
    __tablename__ = 'PlayersT'
    id = Column(Integer, primary_key=True)
    coins = Column(Integer, nullable=True)
    is_registered = Column(Boolean)
    closes = relationship("PlayerClose", back_populates="player")

    def __init__(self, uid, coins):
        self.id = uid
        self.coins = coins
        self.is_registered = False


class Close(Base, SerializerMixin):
    __tablename__ = 'ClosesT'
    id = Column(Integer, primary_key=True, autoincrement=True)
    winner = Column(Enum(Teams))
    players = relationship("PlayerClose", back_populates="close")
    timestamp = Column(DateTime)


class PlayerClose(Base, SerializerMixin):
    __tablename__ = 'PlayerCloseA'
    player_id = Column('player_id', ForeignKey("PlayersT.id"), primary_key=True)
    close_id = Column('close_id', ForeignKey("ClosesT.id"), primary_key=True)
    team = Column(Enum(Teams))
    close = relationship("Close", back_populates="players")
    player = relationship("Player", back_populates="closes")


async def global_init():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def create_session() -> AsyncSession:
    async with __session() as async_session:
        return async_session
