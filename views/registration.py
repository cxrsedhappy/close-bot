import discord
import asyncio

from random import randint
from discord.ext import commands

import settings
from views.captains import CaptainsView


class RegistrationView(discord.ui.View):
    def __init__(self, bot: commands.Bot, new_channel, game, host):
        super().__init__()
        self.timeout = 60 * 60 * 24  # 1 Day
        self.bot = bot
        self.channel = new_channel
        self.game: discord.app_commands.Choice = game
        self.host: discord.Member = host

        self.players: list[discord.Member] = []

    @discord.ui.button(label='Регистрация', style=discord.ButtonStyle.green, custom_id='registration_btn')
    async def registration_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        # Check if user has already registered
        if interaction.user in self.players:
            await interaction.followup.send('Вы уже зарегистрировались', ephemeral=True)
            return

        self.players.append(interaction.user)
        if len(self.players) >= 10:

            button.disabled = True
            self.children[1].disabled = True
            self.children[2].disabled = True
            await interaction.edit_original_response(
                embed=update_embed(self.bot, self.players, self.game, self.host),
                view=self)

            # give players access to category
            guild = interaction.guild
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
                guild.get_role(1112507783993106433): discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

            for player in self.players:
                overwrites[player] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            # Creating category with text and voice channel
            category = await guild.create_category(name=f'close-{self.game.value}', overwrites=overwrites, position=3)
            txt_channel = await guild.create_text_channel(name=f'text-{self.game.value}', category=category)
            vc_channel = await guild.create_voice_channel(name=f'voice-{self.game.value}', category=category)

            # Send message to voice chat
            msg = ''
            for player in self.players:
                msg += f'{player.mention} '
            await txt_channel.send(f'{msg}У вас 5 минуты чтобы зайти в канал {vc_channel}')

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

                msg = ''
                for p in to_ping:
                    msg += f'{p.mention} '

                await txt_channel.send(f'{msg} **не находятся** в голосовом канале. Игра не может быть начата\n'
                                       f'Канал будет удален через 15 секунд.')
                await asyncio.sleep(15)

                await self.channel.delete()
                await txt_channel.delete()
                await vc_channel.delete()
                await category.delete()
                self.stop()
                return

            # Create embed
            captain_team = self.players.pop(randint(0, len(self.players) - 1))
            captain_enemy = self.players.pop(randint(0, len(self.players) - 1))

            emb = discord.Embed(
                title="Выбор игроков", description=f'**Капитаны**: {captain_team.mention} и {captain_enemy.mention}'
            )
            text_player = ''
            for player in self.players:
                text_player += f'{player.mention}\n'
            emb.add_field(name='Игроки', value=text_player)
            emb.set_footer(text=f'Hosted by {self.host.name}')

            wait_view = CaptainsView(
                self.bot, self.players, captain_team, captain_enemy, self.host, txt_channel, vc_channel, emb
            )
            await txt_channel.send(embed=emb, view=wait_view)
            await wait_view.wait()

            await self.channel.delete()
            await txt_channel.delete()
            await vc_channel.delete()
            await category.delete()

            try:
                await wait_view.vc_1.delete()
                await wait_view.vc_2.delete()
            except AttributeError as e:
                print('Ended')

            self.stop()
            return

        await interaction.edit_original_response(embed=update_embed(self.bot, self.players, self.game, self.host), view=self)

    @discord.ui.button(label='Выйти', style=discord.ButtonStyle.red, custom_id='exit_btn')
    async def exit_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players:
            self.players.remove(interaction.user)
        await interaction.response.edit_message(embed=update_embed(self.bot, self.players, self.game, self.host))

    @discord.ui.button(label='Закрыть', style=discord.ButtonStyle.red, custom_id='close_btn')
    async def close_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        if user.guild_permissions.administrator or settings.CLOSER_ROLE in user.roles:
            await interaction.channel.delete()
            self.stop()
            return
        await interaction.response.send_message('У вас нет права', ephemeral=True)


base_url = 'https://cdn.discordapp.com/attachments/1147246596170448896'
images = {
    10: f'{base_url}/1147259700577062962/full.png',
    9: f'{base_url}/1147259698161135746/1.png',
    8: f'{base_url}/1147259698425385030/2.png',
    7: f'{base_url}/1147259698798661682/3.png',
    6: f'{base_url}/1147259699041939517/4.png',
    5: f'{base_url}/1147259699276828772/5.png',
    4: f'{base_url}/1147259699536859286/6.png',
    3: f'{base_url}/1147259699809505491/7.png',
    2: f'{base_url}/1147259700052758579/8.png',
    1: f'{base_url}/1147259700325396520/9.png',
    0: f'{base_url}/1147263693671890985/10.png'
}

games_url = {
    'dota': '/1147574166376169652/dota2close.png',
    'valorant': '/1147574166636200057/valorantclose.png'
}


def update_embed(bot: commands.Bot,
                 players: list[discord.Member],
                 game: discord.app_commands.Choice,
                 host: discord.Member) -> discord.Embed:
    description = ''
    for i, player in enumerate(players, 1):
        description += f'{i}: {player.mention}\n'

    e = discord.Embed(title=f'Игроки ({len(players)} из 10)', description=description)
    e.set_thumbnail(url=images.get(len(players), 0))
    e.set_image(url=f'{base_url}{games_url.get(game.value)}')
    e.set_author(name=f"Регистрация на Клоз по {game.name}", icon_url=bot.application.icon.url)
    e.set_footer(text=f'Hosted by {host.name}')

    return e
