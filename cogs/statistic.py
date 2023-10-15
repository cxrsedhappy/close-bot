import logging
import discord
import settings

from discord import app_commands
from discord.ext import commands

from data.tables import Player

_log = logging.getLogger(__name__)


class StatisticCog(commands.Cog):
    profile = app_commands.Group(name='stats', description='Команды статистики', guild_ids=[settings.SERVER])

    def __init__(self, bot: commands.Bot):
        self._bot = bot

    async def cog_load(self):
        _log.info(f"Loaded {self.__cog_name__}")

    @profile.command(name='voice', description='Профиль пользователя')
    async def voice(self, interaction: discord.Interaction, user: discord.Member = None):
        member = interaction.user

        if user:
            if not user.bot:
                member = user

        player = await Player.get_player(member.id)

        embed = discord.Embed(description=f'> **{player.get_voice_activity()}** часов', colour=2829617)
        embed.set_author(name=f'{member.name}', icon_url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(StatisticCog(bot))
