import discord

from random import randint


class Dropdown(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder='Выберите игрока', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        player = interaction.guild.get_member(int(self.values[0]))
        self.view.picked = player
        self.view.stop()
        await interaction.response.send_message(f'Вы выбрали {player}', ephemeral=True)


class Pick(discord.ui.View):
    def __init__(self, captain: discord.Member, players: list[discord.Member], options: list[discord.SelectOption]):
        super().__init__()
        self._captain = captain

        self.picked: discord.Member = players[randint(0, len(players) - 1)]
        self.add_item(Dropdown(options))

        self.timeout = 60

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user == self._captain

    async def on_timeout(self) -> None:
        self.stop()
