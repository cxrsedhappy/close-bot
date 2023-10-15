import discord

from collections import deque


class RoleInfo(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed], author: discord.Member):
        super().__init__()
        self._info_embed: discord.Embed = embeds.pop(-1)
        self._embeds: list[discord.Embed] = embeds
        self._author = author
        self._init = embeds[0]
        self._queue = deque(self._embeds)
        self._add_pages()

        self.timeout = 20

    def _add_pages(self) -> None:
        for i, embed in enumerate(self._embeds, start=1):
            embed.set_footer(text=f'Страница {i}/{len(self._embeds)}')

    @property
    def init(self) -> discord.Embed:
        return self._init

    @discord.ui.button(label='<-')
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._queue.rotate(1)
        await interaction.response.edit_message(embed=self._queue[0])

    @discord.ui.button(label='->')
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._queue.rotate(-1)
        await interaction.response.edit_message(embed=self._queue[0])

    @discord.ui.button(label='Информация о роли')
    async def info(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.children[0].disabled:
            self.children[0].disabled = True
            self.children[1].disabled = True
            button.label = 'Список носителей'
            await interaction.response.edit_message(embed=self._info_embed, view=self)
        else:
            self.children[0].disabled = False
            self.children[1].disabled = False
            button.label = 'Информация о роли'
            await interaction.response.edit_message(embed=self._queue[0], view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self._author.id
