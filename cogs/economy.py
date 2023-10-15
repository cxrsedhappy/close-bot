import discord
import logging
import settings

from random import randint

from discord import Embed, app_commands
from discord.ext import commands

from views.shop import ShopView

from sqlalchemy import select
from data.db_session import create_session
from data.tables import Player, Role


_log = logging.getLogger(__name__)


class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    async def cog_load(self):
        _log.info(f"Loaded {self.__cog_name__}")

    # @app_commands.guilds(discord.Object(settings.SERVER))
    # @app_commands.command(name='shop', description=f'Магазин ролей')
    # async def shop(self, interaction: discord.Interaction):
    #     embeds = []
    #     embed = Embed(
    #         description='',
    #         colour=2829617
    #     ).set_author(name=f'{interaction.user.name}', icon_url=interaction.user.display_avatar.url)
    #     i = 1
    #     while i - 1 < len(interaction.guild.roles):
    #         role = interaction.guild.roles[i - 1]
    #         _role = await Role.get_role(role.id)
    #         embed.description += f'{i}) {role.mention}\n' \
    #                              f'Продавец: {interaction.guild.get_member(_role.creator_id).mention}\n' \
    #                              f'Продано раз: {_role.purchased}\n' \
    #                              f'Цена: **{_role.price}**\n\n'
    #         if i % 5 == 0:
    #             embeds.append(embed)
    #             embed = Embed(description='', colour=2829617)
    #             embed.set_author(name=f'{interaction.user.name}', icon_url=interaction.user.display_avatar.url)
    #         i += 1
    #     else:
    #         if embed.description != '':
    #             embeds.append(embed)
    #     view = ShopView(embeds, interaction.user)
    #     await interaction.response.send_message(embed=view.init, view=view)

    @app_commands.guilds(discord.Object(settings.SERVER))
    @app_commands.command(name='reward', description=f'Денежная награда')
    @app_commands.checks.cooldown(1, 60 * 60 * 6, key=lambda i: (i.guild_id, i.user.id))
    async def reward(self, interaction: discord.Interaction):
        async with create_session() as session:
            async with session.begin():
                result = await session.execute(select(Player).where(Player.id == interaction.user.id))
                player: Player = result.scalars().first()
                money = randint(50, 150)
                player.coins += money

        embed = Embed(description=f'Вы забрали **{money}** монет', colour=2829617)
        embed.set_author(
            name=f'Временная награда {interaction.user.name}',
            icon_url=interaction.user.display_avatar.url
        )
        await interaction.response.send_message(embed=embed)

    @reward.error
    async def bonus_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            time = int(error.retry_after)

            h = (time // 60) // 60
            m = (time // 60) % 60
            s = time % 60

            embed = Embed(
                description=f'Вы уже забирали награду, следующий раз можно получить через {h}:{m}:{s}', colour=2829617
            )
            embed.set_author(
                name=f'Временная награда {interaction.user.name}',
                icon_url=interaction.user.display_avatar.url
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyCog(bot))
