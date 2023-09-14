import random
import string
import secrets
import discord
import settings

from views.pick import PickView
from views.menu import WinnerView

from utils import BasicEmbed, CaptainEmbed


class CaptainsView(discord.ui.View):
    def __init__(self,
                 t_cap: discord.Member,
                 e_cap: discord.Member,
                 players: list[discord.Member],
                 host: discord.Member,
                 game: discord.app_commands.Choice,
                 text: discord.TextChannel,
                 voice: discord.VoiceChannel):
        super().__init__()

        self.players = players
        self.t_cap = t_cap
        self.e_cap = e_cap
        self.host = host
        self.game = game

        self.text = text
        self.voice = voice
        self.timeout = 60 * 60 * 5  # 5 hours

        self.t_players = []
        self.e_players = []
        self.vc_1 = None
        self.vc_2 = None
        self.active_game = False

    @discord.ui.button(label='Начать', style=discord.ButtonStyle.green, custom_id='registration_btn')
    async def registration_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        button.disabled = True
        await interaction.edit_original_response(view=self)

        turn = False
        data = {'caps': (self.t_cap, self.e_cap), 'teams': (self.t_players, self.e_players)}
        n = len(self.players)
        for i in range(n):
            cap: discord.Member = data['caps'][turn]
            team: list[discord.Member] = data['teams'][turn]

            view = PickView(cap, self.players)
            message: discord.WebhookMessage = await interaction.followup.send(f'{cap.mention}', view=view)
            await view.wait()
            await message.delete()

            player = interaction.guild.get_member(int(view.picked_player))
            team.append(player)
            self.players.remove(player)

            await interaction.edit_original_response(
                embed=CaptainEmbed(data['caps'], self.players, self.host, teams=data['teams']), view=self
            )
            turn = not turn

        # Access to vc
        self.t_players.append(self.t_cap)
        self.e_players.append(self.e_cap)

        self.vc_1 = await self.text.category.create_voice_channel(name=f'team_{self.t_cap}')
        self.vc_2 = await self.text.category.create_voice_channel(name=f'team_{self.e_cap}')
        await self.vc_1.edit(sync_permissions=True)
        await self.vc_2.edit(sync_permissions=True)

        for team, enemy in zip(self.t_players, self.e_players):
            await self.vc_1.set_permissions(target=enemy, overwrite=discord.PermissionOverwrite(connect=False))
            await self.vc_2.set_permissions(target=team, overwrite=discord.PermissionOverwrite(connect=False))

        # Move players to their team voice
        for team, enemy in zip(self.t_players, self.e_players):
            await team.move_to(self.vc_1)
            await enemy.move_to(self.vc_2)

        if self.game.value == 'dota':
            alphabet = string.ascii_letters + string.digits
            lobby = f'discord.gg/5x5_{random.randint(0, 100)}'
            password = ''.join(secrets.choice(alphabet) for _ in range(6))
            await interaction.followup.send(embed=BasicEmbed(lobby, password))

        self.active_game = True
        await interaction.followup.send(f"Удачной игры!")

    @discord.ui.button(label='Завершить', style=discord.ButtonStyle.red, custom_id='exit_btn')
    async def exit_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.active_game:
            await interaction.response.send_message(
                embed=BasicEmbed('Не активная игра', 'Дождитесь окончания пика для завершения'), ephemeral=True
            )
            return

        view = WinnerView(self.t_cap, self.e_cap, self.t_players, self.e_players, self.game, self.host)
        await interaction.response.send_message(view=view, ephemeral=True)
        await view.wait()

        await interaction.channel.send('Завершено')
        await self.vc_1.delete()
        await self.vc_2.delete()

        self.stop()

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator or settings.CLOSER_ROLE in interaction.user.roles:
            return True
        return False
