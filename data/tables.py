from __future__ import annotations

import enum
import datetime

from sqlalchemy import Column, ForeignKey, Table, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy_serializer import SerializerMixin

from data.db_session import Base, create_session


class Teams(enum.Enum):
    team1 = 0
    team2 = 1


class Games(enum.Enum):
    valorant = 0
    dota = 1


class PlayerClose(Base, SerializerMixin):
    __tablename__ = 'APlayerLobby'
    player_id: Mapped[int] = mapped_column('player_id', ForeignKey("Player.id"), primary_key=True)
    player: Mapped[Player] = relationship("Player", back_populates="lobbies", lazy='selectin')
    lobby_id: Mapped[int] = mapped_column('lobby_id', ForeignKey("Lobby.id"), primary_key=True)
    lobby: Mapped[Lobby] = relationship("Lobby", back_populates="players", lazy='selectin')
    team: Mapped[Teams] = mapped_column()

    def __init__(self, team: Teams):
        self.team = team

    def __repr__(self):
        return f'<PlayerClose player_id={self.player_id} lobby_id={self.close_id} team={self.team}>'


class Role(Base, SerializerMixin):
    __tablename__ = 'Role'
    id: Mapped[int] = mapped_column(primary_key=True)
    creator_id: Mapped[int] = mapped_column()
    price: Mapped[int] = mapped_column()
    for_sale: Mapped[bool] = mapped_column(nullable=False)
    purchased: Mapped[int] = mapped_column(nullable=False, default=0)
    expired_at: Mapped[datetime.datetime] = mapped_column(nullable=True)

    def __init__(self, uid, creator, price=0, for_sale=False, expired_at=None):
        self.id = uid
        self.creator_id = creator
        self.price = price
        self.for_sale = for_sale
        self.purchased = 0
        self.expired_at = expired_at

    def __repr__(self):
        return f'<Role name={self.name} creator_id={self.creator_id} price={self.price}>'

    @classmethod
    async def get_role(cls, rid: int) -> Role:
        async with create_session() as session:
            async with session.begin():
                result = await session.execute(select(Role).where(Role.id == rid))
                role = result.scalars().first()
        return role


player_clan = Table(
    "APlayerClan",
    Base.metadata,
    Column("clan_id", ForeignKey("Clan.id"), primary_key=True),
    Column("player_id", ForeignKey("Player.id"), primary_key=True),
)


class Clan(Base, SerializerMixin):
    __tablename__ = 'Clan'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    owner_id: Mapped[int] = mapped_column(nullable=False)
    role_id: Mapped[int] = mapped_column(nullable=False)
    voice_id: Mapped[int] = mapped_column(nullable=False)

    players: Mapped[list[Player]] = relationship(secondary=player_clan, back_populates='clans', lazy='selectin')

    def __init__(self, name, owner_id, role_id, voice_id):
        self.name = name
        self.owner_id = owner_id
        self.role_id = role_id
        self.voice_id = voice_id

    def __repr__(self):
        return f'<Clan id={self.id} name={self.name} owner_id={self.owner_id}>'


class Player(Base, SerializerMixin):
    __tablename__ = 'Player'
    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(nullable=True)
    lobby_nickname: Mapped[str] = mapped_column(nullable=False)
    coins: Mapped[int] = mapped_column(nullable=False, default=0)
    is_registered: Mapped[bool] = mapped_column(default=False)
    is_private: Mapped[bool] = mapped_column(default=False)
    privacy: Mapped[bool] = mapped_column(default=False)
    voice_activity: Mapped[datetime.timedelta] = mapped_column(nullable=False, default=datetime.timedelta())
    joined_vc: Mapped[datetime.datetime] = mapped_column(nullable=True)
    last_seen: Mapped[datetime.datetime] = mapped_column(nullable=True)

    clans: Mapped[list[Clan]] = relationship(secondary=player_clan, back_populates='players', lazy='selectin')
    lobbies: Mapped[list[Lobby]] = relationship("PlayerClose", back_populates="player")

    def __init__(self, uid, nickname):
        self.id = uid
        self.lobby_nickname = nickname

    def __eq__(self, other):
        return isinstance(other, Player) and other.id == self.id

    def __repr__(self):
        return f'<Player id={self.id} coins={self.coins}>'

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

    def get_voice_activity(self) -> str:
        """
        :return: `str` - String representation of voice activity in hours.
        """
        return f'{self.voice_activity.total_seconds() / 3600:.1f}'


class Lobby(Base, SerializerMixin):
    __tablename__ = 'Lobby'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    winner: Mapped[Teams] = mapped_column()
    game: Mapped[Games] = mapped_column()
    timestamp: Mapped[datetime.datetime] = mapped_column()

    players = relationship("PlayerClose", back_populates="lobby")

    def __init__(self, winner, game):
        self.winner = winner
        self.game = game
        self.timestamp = datetime.datetime.now().replace(microsecond=0)

    def __repr__(self):
        return f'<Lobby id={self.id} winner={self.winner} game={self.game} timestamp={self.timestamp}>'


class PrivateRoom(Base, SerializerMixin):
    __tablename__ = 'PrivateRoom'
    id: Mapped[int] = mapped_column(primary_key=True)
    owner: Mapped[int] = mapped_column(nullable=False)

    def __init__(self, cid, owner):
        self.id = cid
        self.owner = owner

    def __repr__(self):
        return f'<PrivateRoom id={self.id} owner={self.owner}>'

    @classmethod
    async def get_room(cls, uid: int) -> PrivateRoom:
        async with create_session() as session:
            async with session.begin():
                room = await session.execute(select(PrivateRoom).where(PrivateRoom.owner == uid))
                room = room.scalars().one_or_none()
        return room
