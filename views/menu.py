import discord
import settings

from discord.app_commands import Choice

from data.tables import Player

from images import games


class Notifications(discord.ui.Select):
    def __init__(self):

        # add emoji='🟩' attribute to SelectOption to add icons
        options = [
            discord.SelectOption(
                label='Уведомления о клозах по Dota 2',
                value='1147633914794479676',
                emoji='<:Valorant:1121405192856928429>'
            ),
            discord.SelectOption(
                label='Уведомления о клозах по Valorant',
                value='1138235016917307432',
                emoji='<:dota:1121404327181946961>'),
        ]

        super().__init__(placeholder='Выберите роль', min_values=0, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(int(self.values[0]))
        embed = discord.Embed(colour=2829617)

        if role in interaction.user.roles:
            embed.description = 'Вы успешно **сняли** роль'
            await interaction.user.remove_roles(role)
        else:
            embed.description = 'Вы успешно **получили** роль'
            await interaction.user.add_roles(role)

        embed.set_author(name='Роли уведомлений', icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.message.edit()


class NotificationsView(discord.ui.View):
    def __init__(self):
        super().__init__()

        notifications = Notifications()
        self.add_item(notifications)
        self.timeout = 60 * 60 * 24 * 31


class Winner(discord.ui.Select):
    def __init__(
            self,
            attackers: list[discord.Member],
            defenders: list[discord.Member],
            options: list[discord.SelectOption],
            game: Choice
    ) -> None:

        self._attackers = attackers
        self._defenders = defenders
        self._game = game

        super().__init__(placeholder='Выберите победителя', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        history_channel = interaction.guild.get_channel(settings.HISTORY_CHANNEL_ID)

        cap1 = await Player.get_player(self._attackers[0].id)
        cap2 = await Player.get_player(self._defenders[0].id)

        winner = f'{cap1.lobby_nickname if int(self.values[0]) == cap1.id else cap2.lobby_nickname}'
        team_value = '\n'.join(player.mention for player in self._attackers)
        enemy_value = '\n'.join(player.mention for player in self._defenders)
        embed = discord.Embed(
            title=f'Close по {self._game.name} завершен',
            description=f'Победитель: **{winner}**',
            colour=2829617
        )
        embed.add_field(name=f'{cap1.lobby_nickname}', value=team_value)
        embed.add_field(name=f'{cap2.lobby_nickname}', value=enemy_value)
        embed.set_image(url=games.get(self._game.value))

        await history_channel.send(embed=embed)
        await interaction.response.send_message('Успешно', ephemeral=True)
        self.view.winner_id = int(self.values[0])
        self.view.stop()


class WinnerView(discord.ui.View):
    def __init__(
            self,
            attackers: list[discord.Member],
            defenders: list[discord.Member],
            options: list[discord.SelectOption],
            game: Choice
    ) -> None:
        super().__init__()
        self.add_item(Winner(attackers, defenders, options, game))
        self.timeout = 60 * 5
        self.winner_id: int = attackers[0].id

    async def on_timeout(self) -> None:
        self.stop()

