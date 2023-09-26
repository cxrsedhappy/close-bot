import discord

from random import randint


class Pick(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder='Выберите игрока', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        player = interaction.guild.get_member(int(self.values[0]))
        self.view.picked = player
        self.view.stop()
        await interaction.response.send_message(f'Вы выбрали {player}', ephemeral=True)


class PickView(discord.ui.View):
    def __init__(self, captain: discord.Member, players: list[discord.Member], options: list[discord.SelectOption]):
        super().__init__()
        self.captain = captain
        self.timeout = 120

        self.add_item(Pick(options))
        self.picked: discord.Member = players[randint(0, len(players) - 1)]

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user == self.captain:
            return True
        return False

    async def on_timeout(self) -> None:
        self.stop()
