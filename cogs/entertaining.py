import logging
import discord
import settings

from discord import app_commands
from discord.ext import commands

from views.registration import RegistrationView
from src.images import images, games_url

_log = logging.getLogger(__name__)


class CloseCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        _log.info(f"Loaded {self.__cog_name__}")

    @app_commands.command(name='create', description='create a file')
    @app_commands.choices(game=[
        app_commands.Choice(name="Valorant", value="valorant"),
        app_commands.Choice(name="Dota 2", value="dota")
    ])
    @app_commands.guilds(discord.Object(settings.SERVER))
    async def create(self, interaction: discord.Interaction, game: discord.app_commands.Choice[str]):
        category = self.bot.get_channel(settings.REG_CATEGORY_ID)
        new_channel = await interaction.guild.create_text_channel(name=f'{game.name}', category=category)

        embed = discord.Embed(title=f'Игроки (0 из 10)', colour=2829617)
        embed.set_author(name=f"Регистрация на Клоз по {game.name}")
        embed.set_thumbnail(url=f'{images.get(0)}')
        embed.set_image(url=f'{games_url.get(game.value)}')
        embed.set_footer(text=f'Hosted by {interaction.user.name}')

        await new_channel.send(embed=embed, view=RegistrationView(new_channel, game, interaction.user))
        await interaction.response.send_message(f'Успешно', ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(CloseCog(bot))
