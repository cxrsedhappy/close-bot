import random
import string
import secrets
import discord
import settings

from views.pick import PickView
from views.menu import WinnerView


class CaptainsView(discord.ui.View):
    def __init__(self,
                 players: list[discord.Member],
                 captain_team: discord.Member,
                 captain_enemy: discord.Member,
                 host: discord.Member,
                 game: discord.app_commands.Choice,
                 text: discord.TextChannel,
                 voice: discord.VoiceChannel,
                 emb: discord.Embed):
        super().__init__()

        self.players = players
        self.captain_team = captain_team
        self.captain_enemy = captain_enemy
        self.host = host
        self.game = game

        self.text = text
        self.voice = voice
        self.embed = emb
        self.timeout = 60 * 60 * 5  # 5 hours

        self.enemy_players = []
        self.team_players = []
        self.vc_1 = None
        self.vc_2 = None

    @discord.ui.button(label='Начать', style=discord.ButtonStyle.green, custom_id='registration_btn')
    async def registration_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        button.disabled = True
        await interaction.edit_original_response(view=self)

        guild = interaction.guild

        """TODO RECODE THIS MESS"""
        for i in range(1):
            # First Captain
            view = PickView(self.players, self.captain_team)
            await interaction.followup.send(f'{self.captain_team.mention}', view=view)
            await view.wait()
            await self.text.purge(limit=1)

            picked_player = guild.get_member(int(view.picked_player))
            self.team_players.append(picked_player)
            self.players.remove(picked_player)

            await interaction.edit_original_response(
                embed=update(
                    self.embed,
                    self.captain_team,
                    self.team_players,
                    self.captain_enemy,
                    self.enemy_players,
                    self.players,
                    self.host
                ),
                view=self
            )

            # Second Captain
            view_2 = PickView(self.players, self.captain_enemy)
            await interaction.followup.send(f'{self.captain_enemy.mention}', view=view_2)
            await view_2.wait()
            await self.text.purge(limit=1)

            picked_player = guild.get_member(int(view_2.picked_player))
            self.enemy_players.append(picked_player)
            self.players.remove(picked_player)

            await interaction.edit_original_response(
                embed=update(
                    self.embed,
                    self.captain_team,
                    self.team_players,
                    self.captain_enemy,
                    self.enemy_players,
                    self.players,
                    self.host
                ),
                view=self
            )

        # Access to vc
        self.team_players.append(self.captain_team)
        self.enemy_players.append(self.captain_enemy)

        self.vc_1 = await self.text.category.create_voice_channel(name=f'team_{self.captain_team}')
        self.vc_2 = await self.text.category.create_voice_channel(name=f'team_{self.captain_enemy}')
        await self.vc_1.edit(sync_permissions=True)
        await self.vc_2.edit(sync_permissions=True)

        for team, enemy in zip(self.team_players, self.enemy_players):
            await self.vc_1.set_permissions(target=enemy, overwrite=discord.PermissionOverwrite(connect=False))
            await self.vc_2.set_permissions(target=team, overwrite=discord.PermissionOverwrite(connect=False))

        # Move players to their team voice
        for team, enemy in zip(self.team_players, self.enemy_players):
            await team.move_to(self.vc_1)
            await enemy.move_to(self.vc_2)

        if self.game.value == 'dota':
            alphabet = string.ascii_letters + string.digits
            lobby = f'discord.gg/5x5_{random.randint(0, 100)}'
            password = ''.join(secrets.choice(alphabet) for _ in range(6))
            embed = discord.Embed(
                title='Лобби в Dota 2', description=f'Название: **{lobby}**\nПароль: **{password}**', colour=2829617
            )
            await interaction.followup.send(embed=embed)

        await interaction.followup.send(f"Удачной игры!")

    @discord.ui.button(label='Завершить', style=discord.ButtonStyle.red, custom_id='exit_btn')
    async def exit_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        winner = WinnerView(
            self.captain_team, self.captain_enemy, self.team_players, self.enemy_players, self.game, self.host
        )
        await interaction.response.send_message(view=winner, ephemeral=True)
        await winner.wait()

        await interaction.channel.send('Завершено')
        await self.vc_1.delete()
        await self.vc_2.delete()

        self.stop()

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator or settings.CLOSER_ROLE in interaction.user.roles:
            return True
        return False


def update(embed: discord.Embed, c_team, team_player, c_enemy, enemy_player, remaining_player, host):
    embed.clear_fields()

    msg = '\n'.join(player.mention for player in remaining_player)
    team = '\n'.join(player.mention for player in team_player)
    enemy = '\n'.join(player.mention for player in enemy_player)

    if msg != '':
        embed.add_field(name='Игроки', value=msg)

    embed.add_field(name=f'team_{c_team}', value=team)
    embed.add_field(name=f'team_{c_enemy}', value=enemy)
    embed.set_footer(text=f'Hosted by {host.name}')

    return embed
