import discord
import settings

from sqlalchemy import select
from data.db_session import Player, create_session


class Info(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.timeout = 60

    @discord.ui.button(label='Профиль', style=discord.ButtonStyle.green)
    async def registration_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Профиль')

    @discord.ui.button(label='История', style=discord.ButtonStyle.red)
    async def exit_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Профиль')

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator or settings.CLOSER_ROLE in interaction.user.roles:
            return True
        return False


class Private(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__()
        self._author: discord.Member = author
        self.timeout = 15

    @discord.ui.button(emoji='✔️')
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with create_session() as session:
            async with session.begin():
                result = await session.execute(select(Player).where(Player.id == interaction.user.id))

                player: Player = result.scalars().first()
                if player.coins < 1000:
                    embed = discord.Embed(description=f'У вас недостаточно **монет**', colour=2829617)
                    embed.set_author(name=f'Изменение приватности {interaction.user.name}',
                                     icon_url=interaction.guild.get_member(player.id).display_avatar.url)
                    await interaction.response.edit_message(embed=embed, view=None)
                    self.stop()
                    return

                player.privacy = True
                player.coins -= 1000

        embed = discord.Embed(description=f'Вы **купили** приватный профиль', colour=2829617)
        embed.set_author(
            name=f'Изменение приватности {interaction.user.name}', icon_url=interaction.user.display_avatar.url)
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(emoji='❌')
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(description=f'Вы **отказались** от покупки', colour=2829617)
        embed.set_author(
            name=f'Изменение приватности {interaction.user.name}', icon_url=interaction.user.display_avatar.url)
        await interaction.response.edit_message(embed=embed, view=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self._author == interaction.user:
            return True
        return False

