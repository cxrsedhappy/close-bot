import logging
import discord

from discord.ext import commands
from views.notifications import NotificationsView

_log = logging.getLogger(__name__)


class TemplateCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        _log.info(f"Loaded {self.__cog_name__}")

    @commands.command(name='notify')
    @commands.has_permissions(administrator=True)
    async def test(self, ctx: commands.Context):
        await ctx.channel.purge(limit=1)
        await ctx.send(view=NotificationsView())


async def setup(bot: commands.Bot):
    await bot.add_cog(TemplateCog(bot))