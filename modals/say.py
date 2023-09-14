import json
import discord

from discord.ui import Modal, TextInput


class CreateEmbed(Modal, title='Embed'):
    json = TextInput(label='JSON', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed.from_dict(json.loads(self.json.value))
        await interaction.response.send_message('Готово', ephemeral=True)
        await interaction.channel.send(embed=embed)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(f'Что-то пошло не так: {error}', ephemeral=True)