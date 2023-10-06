import logging
import discord
import settings

from discord import app_commands
from discord.ext import commands

from data.db_session import Role
from views.role import RoleInfo

_log = logging.getLogger(__name__)


class RoleCog(commands.Cog):
    profile = app_commands.Group(name='role', description='Команды профиля', guild_ids=[settings.SERVER])

    def __init__(self, bot: commands.Bot):
        self._bot = bot

    async def cog_load(self):
        _log.info(f"Loaded {self.__cog_name__}")

    @profile.command(name='info', description='Профиль пользователя')
    async def info(self, interaction: discord.Interaction, role: discord.Role):
        embeds = []

        embed = discord.Embed(title=f'Список носителей роли **{role.name}**', description='', colour=2829617)
        members = role.members
        i = 1
        while i - 1 < len(members):
            embed.description += f'{i}) {members[i - 1].mention}\n'
            if i % 10 == 0:
                embeds.append(embed)
                embed = discord.Embed(title=f'Список носителей роли **{role.name}**', colour=2829617)
            i += 1
        else:
            if embed.description != '':
                embeds.append(embed)

        _role = await Role.get_role(role.id)
        embed = discord.Embed(title=f'Информация о роли "**{role.name}**"', colour=2829617)
        embed.description = f'Роль: {role.mention}\n' \
                            f'Владелец: **{role.guild.get_member(_role.creator_id).mention}**\n' \
                            f'Носителей: **{len(members)}**\n' \
                            f'Продается: {f"**Да**" if _role.for_sale else f"**Нет**"}\n' \
                            f'ID роли: **{role.id}**\n' \
                            f'Цвет роли: **{role.colour}**\n' \
                            f'Действует до: **{f"∞" if not _role.expired_at else _role.expired_at}**'
        embeds.append(embed)
        
        view = RoleInfo(embeds, interaction.user)
        await interaction.response.send_message(embed=view.init, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(RoleCog(bot))
