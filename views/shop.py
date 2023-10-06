import discord

from collections import deque


class ShopView(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed], author: discord.Member):
        super().__init__()
        self._embeds = embeds
        self._author = author

        self._init = embeds[0]
        self._len = len(embeds)
        self._queue = deque(embeds)
        self._add_pages()

        self.timeout = 20

    def _add_pages(self) -> None:
        for i, embed in enumerate(self._embeds, start=1):
            embed.set_footer(text=f'Страница {i}/{self._len}')

    @property
    def init(self) -> discord.Embed:
        return self._init

    @discord.ui.button(label='<-')
    async def previous(self, interaction: discord.Interaction, btn: discord.Button):
        self._queue.rotate(1)
        await interaction.response.edit_message(embed=self._queue[0])

    @discord.ui.button(label='Удалить')
    async def delete(self, interaction: discord.Interaction, btn: discord.Button):
        await interaction.message.delete()
        self.stop()

    @discord.ui.button(label='->')
    async def next(self, interaction: discord.Interaction, btn: discord.Button):
        self._queue.rotate(-1)
        await interaction.response.edit_message(embed=self._queue[0])

    async def on_timeout(self) -> None:
        self.children[0].disabled = True
        self.children[1].disabled = True
        self.children[2].disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self._author.id:
            return True
        return False
