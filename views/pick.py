import discord

from random import randint


class PickPlayer(discord.ui.Select):
    def __init__(self, players: list[discord.Member]):

        options = [
            discord.SelectOption(
                label=f'{player.name}',
                description='',
                value=f'{player.id}')
            for player in players
        ]

        super().__init__(placeholder='Выберите игрока', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.picked_player = int(self.values[0])
        await interaction.response.send_message(
            f'Вы выбрали {interaction.guild.get_member(int(self.values[0])).name}', ephemeral=True
        )
        self.view.stop()


class PickView(discord.ui.View):
    def __init__(self, players: list[discord.Member], captain):
        super().__init__()
        self.players = players
        self.captain = captain
        self.timeout = 60 * 3

        dropdown = PickPlayer(self.players)
        self.add_item(dropdown)
        self.picked_player = self.players[randint(0, len(self.players) - 1)]

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user == self.captain:
            return True
        return False
