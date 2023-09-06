import logging
import discord

from discord import app_commands
from discord.ext import commands

import settings
from views.menu import NotificationsView
from modals.say import Emb

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

    @app_commands.command(name='say', description='creates an embed')
    @app_commands.guilds(discord.Object(settings.SERVER))
    async def say(self, interaction: discord.Interaction):
        await interaction.response.send_modal(Emb())


async def setup(bot: commands.Bot):
    await bot.add_cog(TemplateCog(bot))