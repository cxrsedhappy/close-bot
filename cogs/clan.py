import logging
import discord
import settings

from discord import app_commands
from discord.ext import commands

from views.clan import ClanInfo, Invite

from sqlalchemy import select
from data.db_session import create_session
from data.tables import Clan, Player

_log = logging.getLogger(__name__)


class ClanCog(commands.Cog):
    clan = app_commands.Group(name='clan', description='Команды клана', guild_ids=[settings.SERVER])

    def __init__(self, bot: commands.Bot):
        self._bot = bot

    async def cog_load(self):
        _log.info(f"Loaded {self.__cog_name__}")

    @clan.command(name='create', description='Создать клан')
    async def create(self, interaction: discord.Interaction, name: str):
        role = await interaction.guild.create_role(name=name, colour=234234)

        async with create_session() as session:
            async with session.begin():
                result = await session.execute(select(Clan).where(Clan.owner_id == interaction.user.id))
                clan: Clan = result.scalars().first()
                if clan:
                    await interaction.response.send_message(f'У вас уже есть клан {clan.name}')
                    return

                overwrites = {
                    interaction.guild.default_role: discord.PermissionOverwrite(connect=False),
                    interaction.guild.get_role(role.id): discord.PermissionOverwrite(connect=True)
                }
                await interaction.user.add_roles(role)
                voice = await interaction.guild.categories[7].create_voice_channel(name=name, overwrites=overwrites)
                player = await Player.get_player(interaction.user.id)

                clan = Clan(name, interaction.user.id, role.id, voice.id)
                clan.players.append(player)
                session.add(clan)

                await interaction.response.send_message('Готово', ephemeral=True)

    @clan.command(name='add', description='Добавить пользователя в клан')
    async def add(self, interaction: discord.Interaction, user: discord.Member):
        if user.bot or user.id == interaction.user.id:
            await interaction.response.send_message('Неправильный пользователь', ephemeral=True)
            return

        async with create_session() as session:
            async with session.begin():
                result = await session.execute(select(Clan).where(Clan.owner_id == interaction.user.id))
                clan: Clan = result.scalars().first()
                if clan:
                    player = await Player.get_player(user.id)
                    if player in clan.players:
                        await interaction.response.send_message(
                            f'Пользователь {user.mention} уже в клане', ephemeral=True)
                        return
                    embed = discord.Embed(
                        description=f'Пользователь {interaction.user.mention} приглашает вас в клан {clan.name}',
                        colour=2829617)
                    embed.set_author(name='Приглашение', icon_url=user.display_avatar.url)
                    view = Invite(interaction.user, user, embed)
                    await interaction.response.send_message(f'{user.mention}', embed=view.init, view=view)
                    return
                await interaction.response.send_message('Вы не владеете кланом', ephemeral=True)

    @clan.command(name='remove', description='Удалить пользователя из клана')
    async def remove(self, interaction: discord.Interaction, user: discord.Member):
        if user.bot or user.id == interaction.user.id:
            await interaction.response.send_message('Неправильный пользователь', ephemeral=True)
            return

        async with create_session() as session:
            async with session.begin():
                result = await session.execute(select(Clan).where(Clan.owner_id == interaction.user.id))
                clan: Clan = result.scalars().first()
                if clan:
                    player = await Player.get_player(user.id)
                    if player not in clan.players:
                        await interaction.response.send_message(
                            f'Пользователь {user.mention} не в клане', ephemeral=True)
                        return
                    clan.players.remove(player)
                    await user.remove_roles(interaction.guild.get_role(clan.role_id))
                    await interaction.response.send_message(f'Пользователь {user.mention} выгнан из клана', ephemeral=True)
                    return
                await interaction.response.send_message('Вы не владеете кланом', ephemeral=True)

    @clan.command(name='info', description='Информация о клане')
    async def info(self, interaction: discord.Interaction):
        async with create_session() as session:
            async with session.begin():
                result = await session.execute(select(Clan).where(Clan.owner_id == interaction.user.id))
                clan: Clan = result.scalars().first()
                if not clan:
                    await interaction.response.send_message('Вы не владеете кланом', ephemeral=True)
                    return

                owner = interaction.guild.get_member(clan.owner_id)
                info_embed = discord.Embed(description='', colour=2829617)
                info_embed.set_author(name=f'{clan.name}', icon_url=owner.display_avatar.url)
                info_embed.description += f'Владелец: {owner.mention}\n' \
                                          f'Участники: {len(clan.players)}\n' \
                                          f'Роль: {interaction.guild.get_role(clan.role_id).mention}'

                # Members
                members_embed = discord.Embed(description='', colour=2829617)
                members_embed.set_author(name=f'Информация об участниках клана')
                for i, player in enumerate(clan.players, start=1):
                    members_embed.description += f'{i}) {interaction.guild.get_member(player.id).mention}\n'

                view = ClanInfo(interaction.user, info_embed, members_embed)
                await interaction.response.send_message(embed=view.init, view=view)

    @clan.command(name='colour', description='Изменить цвет роли клана')
    async def colour(self, interaction: discord.Interaction, colour: int):
        if not 0 <= colour <= 16777214:
            await interaction.response.send_message(f'Цвет должен быть в промежутке с 0 до 16777214', ephemeral=True)
            return

        async with create_session() as session:
            async with session.begin():
                result = await session.execute(select(Clan).where(Clan.owner_id == interaction.user.id))
                clan: Clan = result.scalars().first()
                if clan:
                    role = interaction.guild.get_role(clan.role_id)
                    await role.edit(colour=colour)
                    await interaction.response.send_message(
                        f'Вы успешно изменили цвет роли на {role.colour}', ephemeral=True)
                    return
                await interaction.response.send_message('Вы не владеете кланом', ephemeral=True)

    @clan.command(name='delete', description='Удалить клан')
    async def delete(self, interaction: discord.Interaction):
        async with create_session() as session:
            async with session.begin():
                result = await session.execute(select(Clan).where(Clan.owner_id == interaction.user.id))
                clan: Clan = result.scalars().first()
                if clan:
                    await interaction.guild.get_role(clan.role_id).delete()
                    await interaction.guild.get_channel(clan.voice_id).delete()
                    await session.delete(clan)
                    await interaction.response.send_message(f'Вы удалили свой клан', ephemeral=True)
                    return
                await interaction.response.send_message('У вас нет клана', ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ClanCog(bot))
