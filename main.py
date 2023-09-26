import os
import asyncio
import discord
import logging
import settings

from discord.ext import commands

from sqlalchemy import select
from data.db_session import global_init, create_session, Player


_log = logging.getLogger(__name__)


class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='.', intents=discord.Intents.all(), application_id=settings.APP_ID)

    async def setup_hook(self) -> None:
        for fn in os.listdir("./cogs"):
            if fn.endswith(".py"):
                await client.load_extension(f'cogs.{fn[:-3]}')

        # await self.tree.sync(guild=discord.Object(settings.SERVER))
        _log.info("Commands synced")

    async def on_ready(self) -> None:
        await global_init()

        session = await create_session()
        for member in self.get_guild(settings.SERVER).members:
            if not member.bot:
                exists = await session.execute(select(Player).where(Player.id == member.id))
                if exists.scalar() is None:
                    session.add(Player(member.id, f'team_{member.name}'))

        await session.commit()
        await session.close()

        activity = discord.Activity(name="Боже, храни Америку", type=discord.ActivityType.playing)
        await client.change_presence(activity=activity)
        _log.info('on_ready done')

    async def on_member_join(self, member: discord.Member):
        session = await create_session()

        exists = await session.execute(select(Player).where(Player.id == member.id))
        if exists.scalar() is None:
            session.add(Player(member.id, f'team_{member.name}'))

        await session.commit()
        await session.close()


async def main():
    discord.utils.setup_logging()
    await client.start(settings.TOKEN)


if __name__ == '__main__':
    client = Client()
    asyncio.run(main())
