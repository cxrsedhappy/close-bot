import logging
import os
import secrets
import string

import discord
import settings

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from discord import app_commands
from discord.ext import commands

from views.profile import Private

from sqlalchemy import select
from data.db_session import Player, create_session, Lobby

_log = logging.getLogger(__name__)


class ProfileCog(commands.Cog):
    profile = app_commands.Group(name='profile', description='Команды профиля', guild_ids=[settings.SERVER])

    def __init__(self, bot: commands.Bot):
        self._bot = bot

    async def cog_load(self):
        _log.info(f"Loaded {self.__cog_name__}")

    @profile.command(name='info', description='Профиль пользователя')
    async def info(self, interaction: discord.Interaction, user: discord.Member = None):
        if user:
            if user.bot:
                return

        player = await Player.get_player(interaction.user.id if not user else user.id)
        wins = await player.get_wins()
        loses = await player.get_loses()

        matches = len(wins) + len(loses)
        try:
            win_rate = f'{(len(wins) / matches) * 100:.2f}%'
        except ZeroDivisionError:
            win_rate = '0.00%'

        member = interaction.guild.get_member(player.id)

        background = Image.open('src/profile.png')
        draw = ImageDraw.Draw(background)
        font = ImageFont.truetype('src/Montserrat-Regular.ttf', 55)

        # Add info
        pfp = Image.open(BytesIO(await member.display_avatar.read()))
        pfp = pfp.resize((140, 140))
        background.paste(pfp, (190, 125))
        draw.text((347, 120), f"{member.name}", fill=(255, 255, 255), font=font)
        draw.text((400, 359), f"{player.coins}", fill=(255, 255, 255), font=font)
        draw.text((674, 546), f"{player.lobby_nickname}", fill=(255, 255, 255), font=font)
        draw.text((1210, 115), f"{matches}", fill=(255, 255, 255), font=font)
        draw.text((1243, 200), win_rate, fill=(255, 255, 255), font=font)

        if player.is_private and not player.id == interaction.user.id and \
                not interaction.user.guild_permissions.administrator:
            blur = Image.new("L", background.size, 0)
            draw = ImageDraw.Draw(blur)
            draw.rectangle((0, 0, 1600, 800), fill=0)
            blur.putalpha(160)
            background = background.filter(ImageFilter.GaussianBlur(radius=20))
            foreground = Image.open("src/lock.png")
            background.paste(blur, (0, 0), blur.convert('RGBA'))
            background.paste(foreground, (0, 0), foreground.convert('RGBA'))

        alphabet = string.ascii_letters + string.digits
        name = ''.join(secrets.choice(alphabet) for _ in range(6))
        background.save(f'src/{name}.jpg')

        await interaction.response.send_message(
            file=discord.File(f'src/{name}.jpg'),
            ephemeral=True
            if player.is_private and (
                    (player.id == interaction.user.id) or
                    (player.id != interaction.user.id and interaction.user.guild_permissions.administrator)
            ) else False
        )
        os.remove(f'src/{name}.jpg')

    @profile.command(name='team', description='Изменить название команды')
    async def team(self, interaction: discord.Interaction, name: str):
        async with create_session() as session:
            async with session.begin():
                result = await session.execute(select(Player).where(Player.id == interaction.user.id))
                player: Player = result.scalars().first()
                player.lobby_nickname = name

        embed = discord.Embed(description='Название команды **успешно** изменено', colour=2829617)
        embed.set_author(name=f'Профиль {interaction.user.name}', icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @profile.command(name='private', description='Закрыть/Открыть профиль')
    async def private(self, interaction: discord.Interaction):
        async with create_session() as session:
            async with session.begin():
                result = await session.execute(select(Player).where(Player.id == interaction.user.id))
                player: Player = result.scalars().first()
                if not player.privacy:
                    embed = discord.Embed(
                        description=f'Стоимость закрытого профиля **1000** монет навсегда', colour=2829617)
                    embed.set_author(name=f'Изменение приватности {interaction.user.name}',
                                     icon_url=interaction.guild.get_member(player.id).display_avatar.url)
                    await interaction.response.send_message(embed=embed, view=Private(interaction.user))
                    return

                player.is_private = not player.is_private

        embed = discord.Embed(
            description=f'Вы изменили свой профиль на **{f"Закрытый" if player.is_private else f"Открытый"}**',
            colour=2829617
        )
        embed.set_author(
            name=f'Изменение приватности {interaction.user.name}',
            icon_url=interaction.guild.get_member(player.id).display_avatar.url
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ProfileCog(bot))
