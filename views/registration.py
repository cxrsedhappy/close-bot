import asyncio
import discord

from random import randint

from sqlalchemy import select
from data.db_session import create_session, Player

from views.captains import CaptainsView
from src.images import images, games_url


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
            await interaction.followup.send('Вы уже зарегистрировались', ephemeral=True)
            return

        session = await create_session()
        player = await session.execute(select(Player).where(Player.id == interaction.user.id))
        player = player.scalar()
        if player.is_registered:
            await interaction.followup.send('Вы уже зарегистрировались на другой клоз', ephemeral=True)
            return

        player.is_registered = True
        self.players.append(interaction.user)
        await session.commit()
        await session.close()

        await interaction.edit_original_response(embed=update(self.players, self.game, self.host), view=self)
        if len(self.players) >= 4:

            button.disabled = True
            self.children[1].disabled = True
            self.children[2].disabled = True
            await interaction.edit_original_response(
                embed=update(self.players, self.game, self.host),
                view=self
            )

            # give players access to category
            guild = interaction.guild
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=False,
                    manage_channels=False,
                    connect=False
                ),
                guild.get_role(1112507783993106433): discord.PermissionOverwrite(
                    deafen_members=True,
                    move_members=True,
                    mute_members=True,
                    read_messages=True,
                    send_messages=True,
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

            # Voice check
            state = False
            to_ping = []
            for i in range(19):
                await asyncio.sleep(15)
                to_ping = list(set(self.players) - set(vc_channel.members))

                if not to_ping:
                    state = True
                    break

                for p in to_ping:
                    await txt_channel.send(f'Пользователь {p.mention} **не находится** в голосовом чате')
                await txt_channel.send('*Ожидаем пользователей в голосовом чате...*')

            """TODO: REMOVE THIS FUCKING WORKAROUND"""
            if not state:
                msg = ' '.join(player.mention for player in to_ping)
                await txt_channel.send(f'{msg} **не находятся** в голосовом канале. Игра не может быть начата\n'
                                       f'Канал будет удален через 10 секунд.')
                await asyncio.sleep(10)
                await txt_channel.delete()
                await vc_channel.delete()
                await category.delete()
                self.stop()
                return

            # Create embed
            captain_team = self.players.pop(randint(0, len(self.players) - 1))
            captain_enemy = self.players.pop(randint(0, len(self.players) - 1))

            emb = discord.Embed(
                title="Выбор игроков",
                description=f'**Капитаны**: {captain_team.mention} и {captain_enemy.mention}',
                colour=2829617
            )
            txt = '\n'.join(player.mention for player in self.players)
            emb.add_field(name='Игроки', value=txt)
            emb.set_footer(text=f'Hosted by {self.host.name}')

            captain_view = CaptainsView(
                self.players, captain_team, captain_enemy, self.host, self.game, txt_channel, vc_channel, emb
            )

            await txt_channel.send(embed=emb, view=captain_view)
            await captain_view.wait()

            await txt_channel.delete()
            await vc_channel.delete()
            await category.delete()
            await self.channel.delete()

            self.stop()
            return

    @discord.ui.button(label='Выйти', style=discord.ButtonStyle.red, custom_id='exit_btn')
    async def exit_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players:
            self.players.remove(interaction.user)

            session = await create_session()
            player = await session.execute(select(Player).where(Player.id == interaction.user.id))
            player = player.scalar()
            player.is_registered = False
            await session.commit()
            await session.close()

        await interaction.response.edit_message(embed=update(self.players, self.game, self.host))

    @discord.ui.button(label='Закрыть', style=discord.ButtonStyle.red, custom_id='close_btn')
    async def close_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.guild_permissions.administrator is True or self.host == interaction.user:

            session = await create_session()
            for player in self.players:
                p = await session.execute(select(Player).where(Player.id == player.id))
                p = p.scalar()
                p.is_registered = False

            await session.commit()
            await session.close()

            await self.channel.delete()
            self.stop()
            return
        await interaction.response.send_message('У вас нет права', ephemeral=True)

    async def on_timeout(self) -> None:
        await self.channel.delete()


def update(players: list[discord.Member],
           game: discord.app_commands.Choice,
           host: discord.Member) -> discord.Embed:

    description = ''
    for i, player in enumerate(players, 1):
        description += f'{i}: {player.mention}\n'

    embed = discord.Embed(title=f'Игроки ({len(players)} из 10)', description=description, colour=2829617)
    embed.set_thumbnail(url=images.get(len(players), 0))
    embed.set_image(url=f'{games_url.get(game.value)}')
    embed.set_author(name=f"Регистрация на Клоз по {game.name}")
    embed.set_footer(text=f'Hosted by {host.name}')

    return embed
