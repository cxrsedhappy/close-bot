import logging
import discord
import settings

from discord import app_commands
from discord.ext import commands

from utils import basic_embed

from data.db_session import create_session, PlayerClose, Lobby, Player
from sqlalchemy import select


_log = logging.getLogger(__name__)


class ProfileCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        _log.info(f"Loaded {self.__cog_name__}")

    @app_commands.command(name='profile', description='Профиль пользователя')
    @app_commands.guilds(discord.Object(settings.SERVER))
    async def profile(self, interaction: discord.Interaction):
        session = await create_session()

        # Player
        result = await session.execute(select(Player).where(Player.id == interaction.user.id))
        player: Player = result.scalars().first()

        # Wins
        result = await session.execute(
            select(PlayerClose).join(Lobby)
            .where(PlayerClose.player_id == player.id)
            .where(PlayerClose.team == Lobby.winner)
        )
        wins = len(result.scalars().fetchall())

        # Loses
        result = await session.execute(
            select(PlayerClose).join(Lobby)
            .where(PlayerClose.player_id == player.id)
            .where(PlayerClose.team != Lobby.winner)
        )
        loses = len(result.scalars().fetchall())
        await session.close()

        embed = basic_embed()
        embed.set_author(name=f'Профиль {interaction.user.name}', icon_url=interaction.user.avatar.url)
        embed.add_field(name='Монеты', value=f'{player.coins}')
        embed.add_field(name='Имя лобби', value=f'{player.lobby_nickname}')
        embed.add_field(name='Победы', value=f'{wins}')
        embed.add_field(name='Проигрыши', value=f'{loses}')

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ProfileCog(bot))
