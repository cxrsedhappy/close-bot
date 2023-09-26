import discord
from discord.app_commands import Choice
from sqlalchemy import select

import settings
from data.db_session import create_session, Player

from utils import basic_embed, games


class Notifications(discord.ui.Select):
    def __init__(self):

        # add emoji='🟩' attribute to SelectOption to add icons
        options = [
            discord.SelectOption(
                label='Уведомления о клозах по Dota 2',
                value='1147633914794479676',
                emoji='<:Valorant:1121405192856928429>'
            ),
            discord.SelectOption(
                label='Уведомления о клозах по Valorant',
                value='1138235016917307432',
                emoji='<:dota:1121404327181946961>'),
        ]

        super().__init__(placeholder='Выберите роль', min_values=0, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(int(self.values[0]))
        embed = discord.Embed(colour=2829617)

        if role in interaction.user.roles:
            embed.description = 'Вы успешно **сняли** роль'
            await interaction.user.remove_roles(role)
        else:
            embed.description = 'Вы успешно **получили** роль'
            await interaction.user.add_roles(role)

        embed.set_author(name='Роли уведомлений', icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.message.edit()


class NotificationsView(discord.ui.View):
    def __init__(self):
        super().__init__()

        notifications = Notifications()
        self.add_item(notifications)
        self.timeout = 60 * 60 * 24 * 31


class Winner(discord.ui.Select):
    def __init__(self, attackers: list[discord.Member], defenders: list[discord.Member], game: Choice):

        self.attackers = attackers
        self.defenders = defenders
        self.game = game

        options = [
            discord.SelectOption(label=f'team_{self.attackers[0].name}', value=f'{self.attackers[0].id}'),
            discord.SelectOption(label=f'team_{self.defenders[0].name}', value=f'{self.defenders[0].id}'),
        ]

        super().__init__(placeholder='Выберите победителя', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        history_channel = interaction.guild.get_channel(settings.HISTORY_CHANNEL_ID)

        session = await create_session()

        result = await session.execute(select(Player).where(Player.id == self.attackers[0].id))
        cap1: Player = result.scalars().one_or_none()
        result = await session.execute(select(Player).where(Player.id == self.defenders[0].id))
        cap2: Player = result.scalars().one_or_none()

        winner = f'{cap1.lobby_nickname if int(self.values[0]) == cap1.id else cap2.lobby_nickname}'
        team_value = '\n'.join(player.mention for player in self.attackers)
        enemy_value = '\n'.join(player.mention for player in self.defenders)
        embed = basic_embed(f'Close по {self.game.name} завершен', f'Победитель: **{winner}**')
        embed.add_field(name=f'{cap1.lobby_nickname}', value=team_value)
        embed.add_field(name=f'{cap2.lobby_nickname}', value=enemy_value)
        embed.set_image(url=games.get(self.game.value))

        await session.close()

        await history_channel.send(embed=embed)
        await interaction.response.send_message('Успешно', ephemeral=True)
        self.view.winner = int(self.values[0])
        self.view.stop()


class WinnerView(discord.ui.View):
    def __init__(self, attackers: list[discord.Member], defenders: list[discord.Member], game: Choice):
        super().__init__()

        dropdown = Winner(attackers, defenders, game)
        self.add_item(dropdown)
        self.timeout = 60 * 5
        self.winner: int = attackers[0].id

    async def on_timeout(self) -> None:
        self.stop()

