import discord
import settings

from src.images import games_url


class Notifications(discord.ui.Select):
    def __init__(self):

        # add emoji='🟩' attribute to SelectOption to add icons
        options = [
            discord.SelectOption(label='Уведомления о клозах по Dota 2', value='1147633914794479676'),
            discord.SelectOption(label='Уведомления о клозах по Valorant', value='1138235016917307432'),
        ]

        super().__init__(placeholder='Выберите уведомления', min_values=0, max_values=2, options=options)

    async def callback(self, interaction: discord.Interaction):
        """TODO: Optimize it"""
        await interaction.user.remove_roles(
            interaction.guild.get_role(1147633914794479676),
            interaction.guild.get_role(1138235016917307432)
        )

        for value in self.values:
            role = interaction.guild.get_role(int(value))
            await interaction.user.add_roles(role)

        embed = discord.Embed(description='Вы успешно **получили** роль')
        embed.set_author(name='Получение роли уведомлений', icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class NotificationsView(discord.ui.View):
    def __init__(self):
        super().__init__()

        notifications = Notifications()
        self.add_item(notifications)
        self.timeout = 60 * 60 * 24 * 31


class Winner(discord.ui.Select):
    def __init__(self,
                 team_captain: discord.Member,
                 enemy_captain: discord.Member,
                 team_players: list[discord.Member],
                 enemy_players: list[discord.Member],
                 game: discord.app_commands.Choice,
                 host: discord.Member):

        self.team_captain = team_captain
        self.enemy_captain = enemy_captain
        self.team_players = team_players
        self.enemy_players = enemy_players
        self.game = game
        self.host = host

        options = [
            discord.SelectOption(label=f'team_{self.team_captain.name}', value=f'{self.team_captain.id}'),
            discord.SelectOption(label=f'team_{self.enemy_captain.name}', value=f'{self.enemy_captain.id}'),
        ]

        super().__init__(placeholder='Выберите победителя', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        history_channel = interaction.guild.get_channel(settings.HISTORY_CHANNEL_ID)

        team_value = '\n'.join(player.mention for player in self.team_players)
        enemy_value = '\n'.join(player.mention for player in self.enemy_players)
        winner = f'team_{self.team_captain.name}' \
            if self.values[0] == self.team_captain.id else \
            f'team_{self.enemy_captain.name}'

        embed = discord.Embed(title=f'Close по {self.game.name} завершен',
                              description=f'Победитель: ***{winner}***', colour=2829617)
        embed.add_field(name=f'team_{self.team_captain.name}', value=team_value)
        embed.add_field(name=f'team_{self.enemy_captain.name}', value=enemy_value)
        embed.set_image(url=f'{games_url.get(self.game.value)}')
        embed.set_footer(text=f'Hosted by {self.host.name}')

        await history_channel.send(embed=embed)
        await interaction.response.send_message('Успешно', ephemeral=True)
        self.view.stop()


class WinnerView(discord.ui.View):
    def __init__(self,
                 team_captain: discord.Member,
                 enemy_captain: discord.Member,
                 team_players: list[discord.Member],
                 enemy_players: list[discord.Member],
                 game: discord.app_commands.Choice,
                 host: discord.Member):
        super().__init__()

        winner = Winner(team_captain, enemy_captain, team_players, enemy_players, game, host)
        self.add_item(winner)
        self.timeout = 60 * 5
