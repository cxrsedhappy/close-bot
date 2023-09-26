import asyncio
import discord

from utils import basic_embed

from sqlalchemy import select
from data.db_session import PrivateRoom, create_session


class PrivateRoomsView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.timeout = 60 * 60 * 24 * 10

    @discord.ui.button(emoji='<:edit:995803494097371307>', style=discord.ButtonStyle.blurple)
    async def edit_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        private_room = await self.get_private_room(interaction.user.id, interaction.user.voice.channel.id)
        if not private_room:
            _ = basic_embed('Ошибка', 'Это не ваша приватная комната')
            await interaction.followup.send(embed=_, ephemeral=True)
            return

        embed = basic_embed('Управление приватной комнатой', 'Чтобы установить **название** комнаты, введите его ниже')
        embed.set_footer(text='У вас есть **15** секунд, затем сообщение будет недействительно.')
        warning = await interaction.followup.send(embed=embed, ephemeral=True)

        def check(message: discord.Message):
            return message.author.id == private_room.owner

        name: discord.Message | str = interaction.user.name
        try:
            name: discord.Message = await interaction.client.wait_for('message', check=check, timeout=15)
            name = name.content
            await warning.edit(embed=basic_embed('Управление приватной комнатой', 'Успешно'))
        except asyncio.TimeoutError:
            await warning.edit(embed=basic_embed('Время кончилось', 'Вы **не успели** изменить имя комнаты'))
            return

        voice: discord.VoiceChannel = interaction.client.get_channel(private_room.id)
        await voice.edit(name=name)

    @discord.ui.button(emoji='<:user_limit:996051636680142948>', style=discord.ButtonStyle.blurple)
    async def user_limit_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        private_room = await self.get_private_room(interaction.user.id, interaction.user.voice.channel.id)
        if not private_room:
            _ = basic_embed('Ошибка', 'Это не ваша приватная комната')
            await interaction.followup.send(embed=_, ephemeral=True)
            return

        embed = basic_embed('Управление приватной комнатой',
                           'Чтобы установить **количество пользователей** в комнате, введите число ниже')
        embed.set_footer(text='У вас есть **15** секунд, затем сообщение будет недействительно.')
        warning = await interaction.followup.send(embed=embed, ephemeral=True)

        def check(message: discord.Message):
            return message.author.id == private_room.owner

        limit: int = 0
        try:
            user_limit: discord.Message = await interaction.client.wait_for('message', check=check, timeout=15)
            if not (user_limit.content.isdigit() and 1 <= int(user_limit.content) <= 99):
                await warning.edit(embed=basic_embed('Управление приватной комнатой', 'Введите число от **1-99**'))
                return
            limit = int(user_limit.content)
            await warning.edit(embed=basic_embed('Управление приватной комнатой', 'Успешно'))
        except asyncio.TimeoutError:
            await warning.edit(embed=basic_embed('Время кончилось', 'Вы не успели изменить количество пользователей'))
            return

        voice: discord.VoiceChannel = interaction.client.get_channel(private_room.id)
        await voice.edit(user_limit=limit)

    async def get_private_room(self, user_id: int, voice_channel_id: int) -> PrivateRoom:
        session = await create_session()
        room = await session.execute(select(PrivateRoom)
                                     .where(PrivateRoom.owner == user_id)
                                     .where(PrivateRoom.id == voice_channel_id))
        room = room.scalars().one_or_none()
        await session.close()
        return room

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.voice is not None:
            if interaction.user.voice.channel.category.id == 1153441782953160795:
                return True
        return False
