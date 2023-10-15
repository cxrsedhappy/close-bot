import discord
from sqlalchemy import select

from data.db_session import create_session
from data.tables import Clan, Player


class ClanInfo(discord.ui.View):
    def __init__(self, author: discord.Member, info: discord.Embed, members: discord.Embed):
        super().__init__()
        self._author = author
        self._info = info
        self._members = members
        self._init = self._info

    @property
    def init(self) -> discord.Embed:
        return self._init

    @discord.ui.button(label='Список участников')
    async def info(self, interaction: discord.Interaction, button: discord.ui.Button):
        if button.label == 'Информация о клане':
            self._init = self._info
            button.label = 'Список участников'
        else:
            self._init = self._members
            button.label = 'Информация о клане'
        await interaction.response.edit_message(embed=self._init, view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self._author == interaction.user


class Invite(discord.ui.View):
    def __init__(self, owner: discord.Member, invited_user: discord.Member, embed: discord.Embed):
        super().__init__()
        self._owner = owner
        self._invited_user = invited_user
        self._embed = embed
        self.timeout = 60 * 10  # 10 minutes

    @property
    def init(self) -> discord.Embed:
        return self._embed

    @discord.ui.button(emoji='✔️', style=discord.ButtonStyle.blurple)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with create_session() as session:
            async with session.begin():
                result = await session.execute(select(Clan).where(Clan.owner_id == self._owner.id))
                clan: Clan = result.scalars().first()
                if clan:
                    player = await Player.get_player(self._invited_user.id)
                    if len(player.clans) >= 3:
                        await interaction.response.send_message('Вы не можете вступить больше чем в 3+ кланов', ephemeral=True)
                        return
                    clan.players.append(player)
                    role = interaction.guild.get_role(clan.role_id)
                    await self._invited_user.add_roles(role)
                    self._embed.description = f'Пользователь {self._invited_user.mention} вступил в клан'
        await interaction.response.edit_message(embed=self.init, view=None)
        self.stop()

    @discord.ui.button(emoji='❌', style=discord.ButtonStyle.blurple)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._embed.description = f'Пользователь {self._invited_user.mention} отказался от приглашения'
        await interaction.response.edit_message(embed=self.init, view=None)
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self._invited_user == interaction.user
