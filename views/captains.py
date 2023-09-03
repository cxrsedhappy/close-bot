import discord
from discord.ext import commands
from views.pick import PickView
import settings


class CaptainsView(discord.ui.View):
    def __init__(self, bot: commands.Bot,
                 players: list[discord.Member],
                 captain_team: discord.Member,
                 captain_enemy: discord.Member,
                 host: discord.Member,
                 text: discord.TextChannel,
                 voice: discord.VoiceChannel,
                 emb: discord.Embed):
        super().__init__()

        self.bot = bot
        self.players = players
        self.captain_team = captain_team
        self.captain_enemy = captain_enemy
        self.host = host

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
        for i in range(4):
            # First Captain
            view = PickView(self.bot, self.players, self.captain_team)
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
            view_2 = PickView(self.bot, self.players, self.captain_enemy)
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
        """TODO: Reformat code"""
        self.team_players.append(self.captain_team)
        self.enemy_players.append(self.captain_enemy)

        self.vc_1 = await self.text.category.create_voice_channel(name=f'team_{self.captain_team}')
        await self.vc_1.edit(sync_permissions=True)
        self.vc_2 = await self.text.category.create_voice_channel(name=f'team_{self.captain_enemy}')
        await self.vc_2.edit(sync_permissions=True)

        for player in self.enemy_players:
            await self.vc_1.set_permissions(target=player, overwrite=discord.PermissionOverwrite(connect=False))

        for player in self.team_players:
            await self.vc_2.set_permissions(target=player, overwrite=discord.PermissionOverwrite(connect=False))

        # Move players to their team voice
        for player in self.team_players:
            await player.move_to(self.vc_1)

        for player in self.enemy_players:
            await player.move_to(self.vc_2)

        await interaction.followup.send(f"Удачной игры!")

    @discord.ui.button(label='Завершить', style=discord.ButtonStyle.red, custom_id='exit_btn')
    async def exit_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.send_message('Завершено')

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator or settings.CLOSER_ROLE in interaction.user.roles:
            return True
        return False


def update(embed: discord.Embed, c_team, team_player, c_enemy, enemy_player, remaining_player, host):
    embed.clear_fields()

    msg = ''
    for p in remaining_player:
        msg += f'{p.mention}\n'

    t = ''
    for p in team_player:
        t += f'{p.mention}\n'

    e = ''
    for p in enemy_player:
        e += f'{p.mention}\n'

    embed.add_field(name='Игроки', value=msg if msg != '' else '`Никого`')
    embed.add_field(name=f'team_{c_team}', value=t)
    embed.add_field(name=f'team_{c_enemy}', value=e)
    embed.set_footer(text=f'{host.name}')

    return embed
