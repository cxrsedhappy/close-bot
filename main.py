import os
import logging
import asyncio
import discord
import settings

from discord.ext import commands


_log = logging.getLogger(__name__)


class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='.', intents=discord.Intents.all(), application_id=settings.APP_ID)

    async def setup_hook(self) -> None:
        for fn in os.listdir("./cogs"):
            if fn.endswith(".py"):
                await client.load_extension(f'cogs.{fn[:-3]}')

        # uncomment it when you're creating new slash command or changing args in slash commands
        # await self.tree.sync(guild=discord.Object(settings.SERVER))
        _log.info("Commands synced")

    async def on_ready(self) -> None:

        # connection = create_session()
        # members = self.get_guild(settings.SERVER).members
        # for member in members:
        #     existed = connection.query(Player).where(Player.id == member.id).all()
        #     if not existed:
        #         connection.add(Player(id=member.id, coins=0))

        # connection.commit()
        # connection.close()

        activity = discord.Activity(name="боже, храни Америку", type=discord.ActivityType.playing)
        await client.change_presence(activity=activity)
        _log.info('on_ready done')


async def main():
    discord.utils.setup_logging()
    await client.start(settings.TOKEN)


if __name__ == '__main__':
    client = Client()
    # global_init('db/database')
    asyncio.run(main())
