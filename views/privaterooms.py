import asyncio
import discord
from discord import Embed

from data.db_session import PrivateRoom


class PrivateRoomsView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.timeout = 60 * 60 * 24 * 10

    @discord.ui.button(emoji='<:edit:995803494097371307>', style=discord.ButtonStyle.blurple)
    async def edit_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        room = await PrivateRoom.get_room(interaction.user.id, interaction.user.voice.channel.id)
        if not room:
            _ = Embed(title='Ошибка', description='Это не ваша приватная комната', colour=2829617)
            await interaction.followup.send(embed=_, ephemeral=True)
            return

        embed = Embed(
            title='Управление приватной комнатой',
            description='Чтобы установить **название** комнаты, введите его ниже',
            colour=2829617
        ).set_footer(text='У вас есть **15** секунд, затем сообщение будет недействительно.')
        warning = await interaction.followup.send(embed=embed, ephemeral=True)

        def check(message: discord.Message):
            return message.author.id == room.owner

        name: str = interaction.user.name
        try:
            msg: discord.Message = await interaction.client.wait_for('message', check=check, timeout=15)
            name = msg.content
            await warning.edit(embed=Embed(
                title='Управление приватной комнатой', description='Успешно', colour=2829617)
            )
        except asyncio.TimeoutError:
            await warning.edit(embed=Embed(
                title='Время кончилось', description='Вы **не успели** изменить имя комнаты', colour=2829617)
            )
            return

        voice: discord.VoiceChannel = interaction.client.get_channel(room.id)
        await voice.edit(name=name)

    @discord.ui.button(emoji='<:user_limit:996051636680142948>', style=discord.ButtonStyle.blurple)
    async def user_limit_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        room = await PrivateRoom.get_room(interaction.user.id, interaction.user.voice.channel.id)
        if not room:
            await interaction.followup.send(
                embed=Embed(title='Ошибка', description='Это не ваша комната', colour=2829617),
                ephemeral=True
            )
            return

        embed = Embed(
            title='Управление приватной комнатой',
            description='Чтобы установить **количество пользователей** в комнате, введите число ниже',
            colour=2829617)
        embed.set_footer(text='У вас есть **15** секунд, затем сообщение будет недействительно.')
        warning = await interaction.followup.send(embed=embed, ephemeral=True)

        # replace with lambda?
        def check(message: discord.Message):
            return message.author.id == room.owner

        limit: int = 0
        try:
            msg: discord.Message = await interaction.client.wait_for('message', check=check, timeout=15)
            if not (msg.content.isdigit() and 1 <= int(msg.content) <= 99):
                await warning.edit(embed=Embed(
                    title='Управление приватной комнатой', description='Введите число от **1-99**', colour=2829617))
                return
            limit = int(msg.content)
            await warning.edit(embed=Embed(
                title='Управление приватной комнатой', description='Успешно', colour=2829617))
        except asyncio.TimeoutError:
            await warning.edit(embed=Embed(
                title='Время кончилось', description='Вы не успели изменить количество пользователей', colour=2829617))
            return

        voice: discord.VoiceChannel = interaction.client.get_channel(room.id)
        await voice.edit(user_limit=limit)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.voice is not None:
            if interaction.user.voice.channel.category.id == 1153441782953160795:
                return True
        return False
