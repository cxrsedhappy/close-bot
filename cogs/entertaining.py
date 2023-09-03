import logging
import discord
import settings

from discord import app_commands
from discord.ext import commands

from views.registration import RegistrationView

_log = logging.getLogger(__name__)


class CloseCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        _log.info(f"Loaded {self.__cog_name__}")

    @app_commands.command(name='create', description='create a file')
    @app_commands.choices(
        game=[
            app_commands.Choice(name="Valorant", value="valorant"),
            app_commands.Choice(name="Dota 2", value="dota"),
        ])
    @app_commands.guilds(discord.Object(settings.SERVER))
    # @app_commands.default_permissions()
    async def create(self, interaction: discord.Interaction, game: discord.app_commands.Choice[str]):

        """
        TODO
        Determine which permission can use this command

        Help:
        https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.app_commands.checks.has_permissions
        """

        category = self.bot.get_channel(settings.REG_CATEGORY_ID)
        new_channel = await interaction.guild.create_text_channel(name=f'{game.name}', category=category)

        base_url = 'https://cdn.discordapp.com/attachments/1147246596170448896'

        games_url = {
            'dota': '/1147574166376169652/dota2close.png',
            'valorant': '/1147574166636200057/valorantclose.png'
        }

        roles = {
            'dota': interaction.guild.get_role(1147633914794479676),
            'valorant': interaction.guild.get_role(1138235016917307432)
        }

        e = discord.Embed(title=f'Игроки (0 из 10)')
        e.set_author(name=f"Регистрация на Клоз по {game.name}", icon_url=self.bot.application.icon.url)
        e.set_thumbnail(url=f'{base_url}/1147263693671890985/10.png')
        e.set_image(url=f'{base_url}{games_url.get(game.value)}')
        e.set_footer(text=f'Hosted by {interaction.user.name}', icon_url=interaction.user.avatar.url)

        await new_channel.send(f'{roles.get(game.value).mention}',
                               embed=e,
                               view=RegistrationView(self.bot, new_channel, game, interaction.user))
        await interaction.response.send_message(f'close-{game.value} зарегистрирован', ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(CloseCog(bot))
