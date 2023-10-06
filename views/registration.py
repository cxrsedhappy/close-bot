import asyncio
import discord
import settings

from random import randint
from discord import Embed

from sqlalchemy import select
from data.db_session import create_session, Player

from images import games, thumbnails
from views.captains import CaptainsView


class RegistrationView(discord.ui.View):
    def __init__(self, game: discord.app_commands.Choice):
        super().__init__()
        self.game: discord.app_commands.Choice = game
        self.timeout = 60 * 60 * 24  # 1 Day

        self.players: list[discord.Member] = []

    def embed(self) -> Embed:
        description = ''
        for i, player in enumerate(self.players, start=1):
            description += f'{i}: {player.mention}\n'

        embed = Embed(title=f'Игроки ({len(self.players)} из 10)', description=description, colour=2829617)
        embed.set_thumbnail(url=thumbnails.get(len(self.players), 0))
        embed.set_image(url=games.get(self.game.value))
        embed.set_author(name=f"Регистрация на Close по {self.game.name}")

        return embed

    @discord.ui.button(label='Регистрация', style=discord.ButtonStyle.green, custom_id='registration_btn')
    async def registration_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        # Check if user has already registered
        if interaction.user in self.players:
            await interaction.followup.send(
                embed=Embed(
                    title='Регистрация',
                    description='Вы уже **зарегистрированы** на данный клоз',
                    colour=2829617
                ),
                ephemeral=True)
            return

        # Check if player registered in another close
        async with create_session() as session:
            async with session.begin():
                result = await session.execute(select(Player).where(Player.id == interaction.user.id))
                player: Player = result.scalars().first()
                if player.is_registered:
                    await interaction.followup.send(
                        embed=Embed(
                            title='Регистрация',
                            description='Вы уже **зарегистрированы** на другой клоз',
                            colour=2829617),
                        ephemeral=True)
                    return
                if len(self.players) <= 1:
                    self.players.append(interaction.user)
                    player.is_registered = True

        await interaction.edit_original_response(embed=self.embed(), view=self)
        if len(self.players) == 2:
            for btn in self.children:
                btn.disabled = True
            await interaction.edit_original_response(embed=self.embed(), view=self)

            # give players access to category
            guild = interaction.guild
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=True, send_messages=False, manage_channels=False, connect=False
                ),
                guild.get_role(settings.CLOSER_ROLE): discord.PermissionOverwrite(
                    deafen_members=True, move_members=True, mute_members=True, read_messages=True,
                    send_messages=True, connect=True
                )
            }

            for player in self.players:
                overwrites[player] = discord.PermissionOverwrite(send_messages=True, connect=True)

            # Creating category with text and voice channel and syncing their perms with category
            category = await guild.create_category(name=f'close-{self.game.value}', overwrites=overwrites, position=3)
            txt_channel = await guild.create_text_channel(name=f'text-{self.game.value}', category=category)
            vc_channel = await guild.create_voice_channel(name=f'voice-{self.game.value}', category=category)

            await txt_channel.edit(sync_permissions=True)
            await vc_channel.edit(sync_permissions=True)

            # Send message to voice chat
            msg = ' '.join(player.mention for player in self.players)
            await txt_channel.send(f'{msg} У вас 10 минут чтобы зайти в канал {vc_channel.mention}')

            # Voice check 5 minutes
            ready = False
            to_ping = []
            for i in range(1):
                await asyncio.sleep(15)
                to_ping = list(set(self.players) - set(vc_channel.members))
                if not to_ping:
                    ready = True
                    break
                for p in to_ping:
                    await txt_channel.send(f'Пользователь {p.mention} **не находится** в голосовом чате')
                await txt_channel.send('*Ожидаем пользователей в голосовом чате...*')

            if not ready:
                msg = ' '.join(player.mention for player in to_ping)
                await txt_channel.send(f'{msg} **не находятся** в голосовом канале. Игра не может быть начата\n'
                                       f'Будет проведен донабор игроков')
                async with create_session() as session:
                    async with session.begin():
                        result = await session.execute(
                            select(Player).where(Player.id.in_(tuple([p.id for p in to_ping])))
                        )
                        __players: list[Player] = result.scalars().fetchall()
                        for p in __players:
                            p.is_registered = False

                for player in to_ping:
                    self.players.remove(player)

                await asyncio.sleep(5)
                await txt_channel.delete()
                await vc_channel.delete()
                await category.delete()

                for btn in self.children:
                    btn.disabled = False
                await interaction.edit_original_response(embed=self.embed(), view=self)
                return

            # Create embed
            attackers: list[discord.Member] = [self.players.pop(randint(0, len(self.players) - 1))]
            defenders: list[discord.Member] = [self.players.pop(randint(0, len(self.players) - 1))]

            view = CaptainsView(attackers, defenders, self.players.copy(), self.game)
            await txt_channel.send(embed=await view.embed(), view=view)
            await view.wait()

            # Delete all channel when close finished
            await vc_channel.delete()
            await txt_channel.delete()
            await category.delete()

            # Delete registration channel
            await interaction.channel.delete()
            self.stop()

    @discord.ui.button(label='Выйти', style=discord.ButtonStyle.red, custom_id='exit_btn')
    async def exit_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players:
            async with create_session() as session:
                async with session.begin():
                    result = await session.execute(select(Player).where(Player.id == interaction.user.id))
                    player: Player = result.scalars().first()
                    player.is_registered = False

            self.players.remove(interaction.user)
            await interaction.response.edit_message(embed=self.embed())
            return

        _ = Embed(title='Регистрация', description='Вы еще **не зарегистрированы** на этот клоз', colour=2829617)
        await interaction.response.send_message(embed=_, ephemeral=True)

    @discord.ui.button(label='Закрыть', style=discord.ButtonStyle.red, custom_id='close_btn')
    async def close_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.guild_permissions.administrator or settings.CLOSER_ROLE in interaction.user.roles:
            async with create_session() as session:
                async with session.begin():
                    result = await session.execute(
                        select(Player).where(Player.id.in_(tuple([p.id for p in self.players])))
                    )
                    players = result.scalars().fetchall()
                    for p in players:
                        p.is_registered = False
            await interaction.channel.delete()
            self.stop()

    async def on_timeout(self) -> None:
        async with create_session() as session:
            async with session.begin():
                result = await session.execute(
                    select(Player).where(Player.id.in_(tuple([p.id for p in self.players])))
                )
                players = result.scalars().fetchall()
                for p in players:
                    p.is_registered = False
