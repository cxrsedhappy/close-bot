import logging
import discord
import datetime
import settings

from discord import app_commands, VoiceState, Member
from discord.ext import commands

from views.privaterooms import PrivateRoomsView

from sqlalchemy import select
from data.db_session import create_session
from data.tables import Player, PrivateRoom

_log = logging.getLogger(__name__)


class PrivateRoomsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    async def cog_load(self):
        _log.info(f"Loaded {self.__cog_name__}")

    @app_commands.command(name='private', description='Создает меню управления приватками')
    @app_commands.guilds(discord.Object(settings.SERVER))
    async def private(self, interaction: discord.Interaction):
        view = PrivateRoomsView()
        embed = discord.Embed(
            title='**Управление приватной комнатой**',
            description='Жми следующие кнопки, чтобы настроить свою комнату\n'
                        'Использовать их можно только когда у тебя есть приватный канал',
            colour=2829617
        )
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message('Готово', ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        # Put context manager here?
        if not before.channel and after.channel:
            async with create_session() as session:
                async with session.begin():
                    result = await session.execute(select(Player).where(Player.id == member.id))
                    player: Player = result.scalars().one_or_none()
                    player.joined_vc = datetime.datetime.now().replace().replace(microsecond=0)

        if before.channel and not after.channel:
            async with create_session() as session:
                async with session.begin():
                    result = await session.execute(select(Player).where(Player.id == member.id))
                    player: Player = result.scalars().one_or_none()
                    player.last_seen = datetime.datetime.now().replace(microsecond=0)

                    # if member was in vc when bot was reloaded
                    if player.joined_vc:
                        player.voice_activity += player.last_seen - player.joined_vc

        # Replace with any()?
        # Checks if member used mute, deaf etc.
        if after.deaf or after.mute or \
                after.self_deaf or after.self_mute or \
                after.self_video or after.self_stream or \
                before.deaf or before.mute or \
                before.self_deaf or before.self_mute or \
                before.self_video or before.self_stream:
            return

        if before.channel and before.channel.category:
            if before.channel.category.id == settings.PRIVATE_ROOMS_CATEGORY_ID and len(before.channel.members) == 0:
                async with create_session() as session:
                    async with session.begin():
                        result = await session.execute(
                            select(PrivateRoom)
                            .where(PrivateRoom.id == before.channel.id)
                        )
                        room: PrivateRoom = result.scalars().one_or_none()
                        if room:
                            await session.delete(room)
                            await before.channel.delete()

        # Create channel when member join create voice channel
        if after.channel and after.channel.id == settings.ENTRY_ROOM_ID:
            async with create_session() as session:
                async with session.begin():
                    room = await PrivateRoom.get_room(member.id)
                    if room:
                        await member.edit(voice_channel=self._bot.get_channel(room.id))
                        return

                    channel = await after.channel.category.create_voice_channel(name=f'{member.name}')
                    session.add(PrivateRoom(channel.id, member.id))
                    await member.move_to(channel)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id == settings.MANAGE_CHANNEL_ID and not message.author.bot:
            await message.delete()


async def setup(bot: commands.Bot):
    await bot.add_cog(PrivateRoomsCog(bot))
