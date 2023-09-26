import asyncio
import discord
import settings

from random import randint

from sqlalchemy import select
from data.db_session import create_session, Player

from utils import basic_embed, reg_embed, cap_embed
from views.captains import CaptainsView


class RegistrationView(discord.ui.View):
    def __init__(self, game: discord.app_commands.Choice):
        super().__init__()
        self.game: discord.app_commands.Choice = game
        self.timeout = 60 * 60 * 24  # 1 Day

        self.players: list[discord.Member] = []

    @discord.ui.button(label='Регистрация', style=discord.ButtonStyle.green, custom_id='registration_btn')
    async def registration_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        # Check if user has already registered
        if interaction.user in self.players:
            await interaction.followup.send(
                embed=basic_embed('Регистрация', 'Вы уже **зарегистрированы** на данный клоз'),
                ephemeral=True)
            return

        # Check if player registered in another close
        session = await create_session()
        result = await session.execute(select(Player).where(Player.id == interaction.user.id))
        player: Player = result.scalars().first()

        if player.is_registered:
            await interaction.followup.send(
                embed=basic_embed('Регистрация', 'Вы уже **зарегистрированы** на другой клоз'),
                ephemeral=True)
            await session.close()
            return

        player.is_registered = True
        await session.commit()
        await session.close()

        self.players.append(interaction.user)
        await interaction.edit_original_response(embed=reg_embed(self.players, self.game), view=self)
        if len(self.players) == 4:

            for btn in self.children:
                btn.disabled = True
            await interaction.edit_original_response(embed=reg_embed(self.players, self.game), view=self)

            # give players access to category
            guild = interaction.guild
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=True, send_messages=False, manage_channels=False, connect=False
                ),
                guild.get_role(1112507783993106433): discord.PermissionOverwrite(
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
            await txt_channel.send(f'{msg}У вас 5 минут чтобы зайти в канал {vc_channel.mention}')

            # Voice check 5 minutes
            ready = False
            to_ping = []
            for i in range(19):
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
                                       f'Канал будет удален через 10 секунд.')
                self.stop()
                session = await create_session()
                result = await session.execute(select(Player).where(Player.id.in_(tuple([p.id for i in self.players]))))
                __players: list[Player] = result.scalars().fetchall()
                for p in __players:
                    p.is_registered = False
                await session.commit()
                await session.close()
                await asyncio.sleep(10)
                await txt_channel.delete()
                await vc_channel.delete()
                await category.delete()
                return

            # Create embed
            purge_list = [p.id for p in self.players]
            attackers: list[discord.Member] = [self.players.pop(randint(0, len(self.players) - 1))]
            defenders: list[discord.Member] = [self.players.pop(randint(0, len(self.players) - 1))]

            embed = cap_embed(attackers, defenders, self.players)
            view = CaptainsView(attackers, defenders, self.players.copy(), self.game)
            await txt_channel.send(embed=embed, view=view)
            await view.wait()

            session = await create_session()
            result = await session.execute(select(Player).where(Player.id.in_(tuple(purge_list))))
            __players: list[Player] = result.scalars().fetchall()
            for p in __players:
                p.is_registered = False
            await session.commit()
            await session.close()

            # Delete all channel when finished
            await vc_channel.delete()
            await txt_channel.delete()
            await category.delete()

            # Delete registration channel
            await interaction.channel.delete()
            self.stop()

    @discord.ui.button(label='Выйти', style=discord.ButtonStyle.red, custom_id='exit_btn')
    async def exit_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players:

            session = await create_session()
            result = await session.execute(select(Player).where(Player.id == interaction.user.id))
            player: Player = result.scalars().one_or_none()
            player.is_registered = False
            await session.commit()
            await session.close()

            self.players.remove(interaction.user)
            await interaction.response.edit_message(embed=reg_embed(self.players, self.game))
            return

        _ = basic_embed('Регистрация', 'Вы еще **не зарегистрированы** на этот клоз')
        await interaction.response.send_message(embed=_, ephemeral=True)

    @discord.ui.button(label='Закрыть', style=discord.ButtonStyle.red, custom_id='close_btn')
    async def close_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.guild_permissions.administrator or settings.CLOSER_ROLE in interaction.user.roles:

            session = await create_session()
            result = await session.execute(select(Player).where(Player.id.in_(tuple([p.id for p in self.players]))))
            players = result.scalars().fetchall()
            for p in players:
                p.is_registered = False
            await session.commit()
            await session.close()

            await interaction.channel.delete()
            self.stop()

    async def on_timeout(self) -> None:
        self.stop()
