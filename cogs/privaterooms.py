import logging
import discord
import settings

from discord import app_commands, VoiceState, Member
from discord.ext import commands

from views.privaterooms import PrivateRoomsView

from sqlalchemy import select
from data.db_session import create_session, PrivateRoom

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
        if after.deaf or after.mute or after.self_deaf or after.self_mute \
                or before.deaf or before.mute or before.self_deaf or before.self_mute:
            return

        # Delete voice channel after owner left
        if before.channel:
            if before.channel.id != 1153441991980494879 and before.channel.category.id == 1153441782953160795:
                async with create_session() as session:
                    async with session.begin():
                        room = await session.execute(
                            select(PrivateRoom)
                            .where(PrivateRoom.owner == member.id)
                            .where(PrivateRoom.id == before.channel.id))
                        room = room.scalars().one_or_none()
                        if room is not None:
                            await session.delete(room)
                            await before.channel.delete()

        # Create channel when member join voice channel
        if after.channel and after.channel.id == 1153441991980494879:
            channel = await after.channel.category.create_voice_channel(name=member.name)

            async with create_session() as session:
                async with session.begin():
                    session.add(PrivateRoom(channel.id, member.id))

            await member.move_to(channel)
            return

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id == 1153441934128467968 and not message.author.bot:
            await message.delete()


async def setup(bot: commands.Bot):
    await bot.add_cog(PrivateRoomsCog(bot))
