import asyncio
from io import BytesIO

from PIL import Image, ImageFilter
from PIL import ImageDraw

import sys

from data.db_session import create_session, Player, Lobby, Teams, PlayerClose
from sqlalchemy import select
from sqlalchemy.orm import selectinload


def a():
    r = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    g = r[10:]
    r = r[:10]
    print(r, g)


async def main():
    # background = Image.open("src/profile.png")
    # blur = Image.new("L", background.size, 0)
    # draw = ImageDraw.Draw(blur)
    # draw.rectangle((0, 0, 1600, 800), fill=0)
    # blur.putalpha(168)
    # background = background.filter(ImageFilter.GaussianBlur(radius=10))
    # foreground = Image.open("src/lock.png")
    # background.paste(blur, (0, 0), blur.convert('RGBA'))
    # background.paste(foreground, (0, 0), foreground.convert('RGBA'))
    # background.show()
    data = [370996968811397122, 423231892943536139, 428188503390814212, 453197176714166273]
    async with create_session() as session:
        async with session.begin():
            for pid in data:
                result = await session.execute(select(Player).where(Player.id == pid))
                p: Player = result.scalars().first()
                print(await p.get_wins(), await p.get_loses())


if __name__ == '__main__':
    a()
