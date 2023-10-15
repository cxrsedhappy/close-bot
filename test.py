import asyncio
from io import BytesIO

from PIL import Image, ImageFilter
from PIL import ImageDraw

import sys

from sqlalchemy import select
from data.db_session import create_session
from data.tables import Player, Lobby, Teams, PlayerClose
from sqlalchemy.orm import selectinload


async def main():
    data = [370996968811397122]
    async with create_session() as session:
        async with session.begin():
            for pid in data:
                result = await session.execute(select(Player).where(Player.id == pid))
                p: Player = result.scalars().first()
                print(p.clans)


if __name__ == '__main__':
    asyncio.run(main())
