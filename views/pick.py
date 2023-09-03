import random
import discord

from random import randint
from discord.ext import commands


class PickPlayer(discord.ui.Select):
    def __init__(self,
                 players: list[discord.Member]):

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
        await interaction.response.send_message(f'Вы пикнули {self.values[0]}', ephemeral=True)
        self.view.stop()


class PickView(discord.ui.View):
    def __init__(self, bot: commands.Bot, players: list[discord.Member], captain):
        super().__init__()
        self.timeout = 60 * 3
        self.bot = bot
        self.players = players
        self.captain = captain

        dropdown = PickPlayer(self.players)
        self.add_item(dropdown)
        self.picked_player = self.players[random.randint(0, len(self.players) - 1)]

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user == self.captain:
            return True
        return False
