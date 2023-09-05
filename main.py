import os
import logging
import asyncio
import discord
import settings

from discord.ext import commands

from data.members import Player
from data.db_session import global_init, create_session


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
        connection = create_session()
        members = self.get_guild(settings.SERVER).members

        for member in members:
            if not member.bot:
                exists = connection.query(Player).where(Player.id == member.id).all()
                if not exists:
                    connection.add(Player(uid=member.id, coins=0))

        connection.commit()
        connection.close()

        activity = discord.Activity(name="Боже, храни Америку", type=discord.ActivityType.playing)
        await client.change_presence(activity=activity)
        _log.info('on_ready done')

    async def on_member_join(self, member: discord.Member):
        connection = create_session()

        exists = connection.query(Player).where(Player.id == member.id).all()
        if not exists:
            connection.add(Player(uid=member.id, coins=0))

        connection.commit()
        connection.close()


async def main():
    discord.utils.setup_logging()
    await client.start(settings.TOKEN)


if __name__ == '__main__':
    client = Client()
    global_init('db/database')
    asyncio.run(main())
