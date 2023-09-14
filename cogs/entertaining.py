import logging
import discord
import settings

from discord import app_commands
from discord.ext import commands

from views.registration import RegistrationView
from utils import RegistrationEmbed

_log = logging.getLogger(__name__)


class CloseCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        _log.info(f"Loaded {self.__cog_name__}")

    @app_commands.command(name='create', description='create a file')
    @app_commands.choices(game=[
        app_commands.Choice(name="Valorant", value="valorant"),
        app_commands.Choice(name="Dota 2", value="dota")])
    @app_commands.guilds(discord.Object(settings.SERVER))
    async def create(self, interaction: discord.Interaction, game: discord.app_commands.Choice[str]):
        category = self.bot.get_channel(settings.REG_CATEGORY_ID)
        new_channel = await interaction.guild.create_text_channel(name=f'{game.name} close', category=category)

        await new_channel.send(
            embed=RegistrationEmbed([], game, interaction.user),
            view=RegistrationView(new_channel, game, interaction.user)
        )
        await interaction.response.send_message(f'Успешно', ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(CloseCog(bot))
