import asyncio

from data.db_session import create_session, Player, Lobby, Teams, PlayerClose
from sqlalchemy import select
from sqlalchemy.orm import selectinload


async def main():

    a = [370996968811397122, 423231892943536139, 428188503390814212, 453197176714166273]

    session = await create_session()

    for player in a:
        result = await session.execute(
            select(Lobby)
            .join(PlayerClose)
            .where(Lobby.winner == PlayerClose.team)
            .where(PlayerClose.player_id == player).options(selectinload(Lobby.players))
        )
        participation: list[Lobby] = result.scalars().fetchall()
        for lobby in participation:
            print(lobby)
            for p in lobby.players:
                print(f'\t{p.player}', end='')
            print()
        print()

    await session.close()

if __name__ == '__main__':
    asyncio.run(main())
