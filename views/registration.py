import asyncio
import discord

from random import randint

from views.captains import CaptainsView
from utils import BasicEmbed, RegistrationEmbed, CaptainEmbed


class RegistrationView(discord.ui.View):
    def __init__(self,
                 channel: discord.TextChannel,
                 game: discord.app_commands.Choice,
                 host: discord.Member):
        super().__init__()
        self.channel: discord.TextChannel = channel
        self.game: discord.app_commands.Choice = game
        self.host: discord.Member = host
        self.timeout = 60 * 60 * 24  # 1 Day

        self.players: list[discord.Member] = []

    @discord.ui.button(label='Регистрация', style=discord.ButtonStyle.green, custom_id='registration_btn')
    async def registration_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        # Check if user has already registered
        if interaction.user in self.players:
            await interaction.followup.send(
                embed=BasicEmbed('Регистрация', 'Вы уже **зарегистрированы** на данный close'),
                ephemeral=True)
            return

        self.players.append(interaction.user)
        await interaction.edit_original_response(embed=RegistrationEmbed(self.players, self.game, self.host), view=self)
        if len(self.players) >= 4:
            button.disabled = True
            self.children[1].disabled = True
            self.children[2].disabled = True
            await interaction.edit_original_response(
                embed=RegistrationEmbed(self.players, self.game, self.host), view=self
            )

            # give players access to category
            guild = interaction.guild
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=True, send_messages=False, manage_channels=False, connect=False
                ),
                guild.get_role(1112507783993106433): discord.PermissionOverwrite(
                    deafen_members=True, move_members=True, mute_members=True, read_messages=True, send_messages=True,
                    connect=True,
                )
            }

            for player in self.players:
                overwrites[player] = discord.PermissionOverwrite(send_messages=True, connect=True)

            # Creating category with text and voice channel and syncing their perms with category
            category = await guild.create_category(name=f'close-{self.game.value}', overwrites=overwrites, position=3)
            txt_channel = await guild.create_text_channel(name=f'text-{self.game.value}', category=category)
            await txt_channel.edit(sync_permissions=True)
            vc_channel = await guild.create_voice_channel(name=f'voice-{self.game.value}', category=category)
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
                await asyncio.sleep(10)
                await txt_channel.delete()
                await vc_channel.delete()
                await category.delete()
                return

            # Create embed
            t_cap: discord.Member = self.players.pop(randint(0, len(self.players) - 1))
            e_cap: discord.Member = self.players.pop(randint(0, len(self.players) - 1))

            embed = CaptainEmbed((t_cap, e_cap), self.players, self.host)
            view = CaptainsView(t_cap, e_cap, self.players, self.host, self.game, txt_channel, vc_channel)
            await txt_channel.send(embed=embed, view=view)
            await view.wait()

            # Delete all channel when finished
            await vc_channel.delete()
            await txt_channel.delete()
            await category.delete()

            # Delete registration channel
            await self.channel.delete()
            self.stop()
            return

    @discord.ui.button(label='Выйти', style=discord.ButtonStyle.red, custom_id='exit_btn')
    async def exit_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players:
            self.players.remove(interaction.user)
            await interaction.response.edit_message(embed=RegistrationEmbed(self.players, self.game, self.host))
            return
        await interaction.response.send_message(
            embed=BasicEmbed('Упс... Что-то не так', 'Вы еще **не зарегистрированы** на этот клоз'), ephemeral=True
        )

    @discord.ui.button(label='Закрыть', style=discord.ButtonStyle.red, custom_id='close_btn')
    async def close_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.guild_permissions.administrator is True or self.host == interaction.user:
            await self.channel.delete()
            self.stop()

    async def on_timeout(self) -> None:
        await self.channel.delete()
