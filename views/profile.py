import discord

from sqlalchemy import select
from data.db_session import create_session
from data.tables import Player


class Private(discord.ui.View):
    def __init__(self, author: discord.Member, embed: discord.Embed):
        super().__init__()
        self._author: discord.Member = author
        self._embed: discord.Embed = embed
        self.timeout = 15

    @discord.ui.button(emoji='✔️', style=discord.ButtonStyle.blurple)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with create_session() as session:
            async with session.begin():
                result = await session.execute(select(Player).where(Player.id == interaction.user.id))
                player: Player = result.scalars().first()

                if player.coins < 1000:
                    self._embed.description=f'У вас недостаточно **монет**'
                    await interaction.response.edit_message(embed=self._embed, view=None)
                    return

                player.privacy = True
                player.coins -= 1000

        self._embed.description = f'Вы **купили** приватный профиль'
        await interaction.response.edit_message(embed=self._embed, view=None)

    @discord.ui.button(emoji='❌', style=discord.ButtonStyle.blurple)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._embed.description = f'Вы **отказались** от покупки'
        await interaction.response.edit_message(embed=self._embed, view=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self._author == interaction.user
