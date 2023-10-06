from __future__ import annotations

import enum
import datetime
import contextlib

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, select
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_serializer import SerializerMixin


Base = declarative_base()
engine = create_async_engine('sqlite+aiosqlite:///db/database?check_same_thread=False', echo=False)
session_factory = async_sessionmaker(engine, expire_on_commit=False)


class Teams(enum.Enum):
    team1 = 0
    team2 = 1


class Games(enum.Enum):
    valorant = 0
    dota = 1


class PlayerClose(Base, SerializerMixin):
    __tablename__ = 'APlayerLobby'
    player_id = Column('player_id', ForeignKey("Player.id"), primary_key=True)
    player = relationship("Player", back_populates="lobbies", lazy='selectin')
    lobby_id = Column('lobby_id', ForeignKey("Lobby.id"), primary_key=True)
    lobby = relationship("Lobby", back_populates="players", lazy='selectin')
    team = Column(Enum(Teams))

    def __init__(self, team: Teams):
        self.team = team

    def __repr__(self):
        return f'PlayerClose<{self.player_id}, {self.close_id}, {self.team}>'


class Role(Base, SerializerMixin):
    __tablename__ = 'Role'
    id = Column(Integer, primary_key=True)
    creator_id = Column(Integer)
    price = Column(Integer)
    for_sale = Column(Boolean, nullable=False)
    purchased = Column(Integer, nullable=False, default=0)
    expired_at = Column(DateTime, nullable=True)

    def __init__(self, uid, creator, price=0, for_sale=False, expired_at=None):
        self.id = uid
        self.creator_id = creator
        self.price = price
        self.for_sale = for_sale
        self.purchased = 0
        self.expired_at = expired_at

    def __repr__(self):
        return f'Role<{self.name}, {self.creator}>'

    @classmethod
    async def get_role(cls, rid: int) -> Role:
        async with create_session() as session:
            async with session.begin():
                result = await session.execute(select(Role).where(Role.id == rid))
                role = result.scalars().first()
        return role


class Player(Base, SerializerMixin):
    __tablename__ = 'Player'
    id = Column(Integer, primary_key=True)
    lobby_nickname = Column(String, nullable=False)
    coins = Column(Integer, nullable=False, default=0)
    is_registered = Column(Boolean, default=False)
    is_private = Column(Boolean, default=False)
    privacy = Column(Boolean, default=False)

    lobbies = relationship("PlayerClose", back_populates="player")

    def __init__(self, uid, nickname):
        self.id = uid
        self.lobby_nickname = nickname

    def __repr__(self):
        return f'Player<{self.id}, {self.coins}, {self.is_registered}>'

    @classmethod
    async def get_player(cls, pid: int) -> Player:
        async with create_session() as session:
            async with session.begin():
                result = await session.execute(select(Player).where(Player.id == pid))
                player: Player = result.scalars().first()
        return player

    async def get_wins(self) -> list[Lobby]:
        async with create_session() as session:
            async with session.begin():
                result = await session.execute(
                    select(Lobby)
                    .join(PlayerClose)
                    .where(Lobby.winner == PlayerClose.team)
                    .where(PlayerClose.player_id == self.id)
                )
                lobbies: list[Lobby] = result.scalars().all()
        return lobbies

    async def get_loses(self) -> list[Lobby]:
        async with create_session() as session:
            async with session.begin():
                result = await session.execute(
                    select(Lobby)
                    .join(PlayerClose)
                    .where(Lobby.winner != PlayerClose.team)
                    .where(PlayerClose.player_id == self.id)
                )
                lobbies: list[Lobby] = result.scalars().all()
        return lobbies


class Lobby(Base, SerializerMixin):
    __tablename__ = 'Lobby'
    id = Column(Integer, primary_key=True, autoincrement=True)
    winner = Column(Enum(Teams))
    game = Column(Enum(Games))
    timestamp = Column(DateTime)

    players = relationship("PlayerClose", back_populates="lobby")

    def __init__(self, winner, game):
        self.winner = winner
        self.game = game
        self.timestamp = datetime.datetime.now().replace(microsecond=0)

    def __repr__(self):
        return f'Lobby<{self.id}, {self.winner}, {self.timestamp}>'


class PrivateRoom(Base, SerializerMixin):
    __tablename__ = 'PrivateRoom'
    id = Column(Integer, primary_key=True)
    owner = Column(Integer, nullable=False)

    def __init__(self, cid, owner):
        self.id = cid
        self.owner = owner

    def __repr__(self):
        return f'PrivateRoom<{self.id}, {self.owner}>'

    @classmethod
    async def get_room(cls, uid: int, vc_id: int) -> PrivateRoom:
        async with create_session() as session:
            async with session.begin():
                room = await session.execute(select(PrivateRoom).where(PrivateRoom.owner == uid).where(PrivateRoom.id == vc_id))
                room = room.scalars().one_or_none()
        return room


async def global_init():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


@contextlib.asynccontextmanager
async def create_session() -> AsyncSession:
    async with session_factory() as session:
        yield session
