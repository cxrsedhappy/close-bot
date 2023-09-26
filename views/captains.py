import random
import string
import secrets
import discord
import settings

from discord import Member
from discord.app_commands import Choice

from views.pick import PickView
from views.menu import WinnerView

from utils import basic_embed, cap_embed

from sqlalchemy import select
from data.db_session import Lobby, Player, PlayerClose, create_session, Teams, Games


class CaptainsView(discord.ui.View):
    def __init__(self, attackers: list[Member], defenders: list[Member], players: list[Member], game: Choice):
        super().__init__()
        self.players = players
        self.game = game

        self.attackers = attackers
        self.defenders = defenders

        self.vc1 = None
        self.vc2 = None
        self.active_game = False

        self.timeout = 60 * 60 * 5  # 5 hours

    @discord.ui.button(label='Начать', style=discord.ButtonStyle.green)
    async def registration_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        button.disabled = True
        await interaction.edit_original_response(view=self)

        turn = False
        teams = (self.attackers, self.defenders)

        n = len(self.players)
        for i in range(n):
            captain: discord.Member = teams[turn][0]
            team: list[discord.Member] = teams[turn]

            # Filling options (Temporary solution)
            # Better create class LobbyPlayer with user and stats to reduce database usage
            options = []
            session = await create_session()
            for member in self.players:
                result = await session.execute(
                    select(PlayerClose).join(Lobby)
                    .where(PlayerClose.player_id == member.id)
                    .where(Lobby.winner == PlayerClose.team)
                )
                wins = len(result.scalars().fetchall())
                result = await session.execute(
                    select(PlayerClose).join(Lobby)
                    .where(PlayerClose.player_id == member.id)
                    .where(Lobby.winner != PlayerClose.team)
                )
                loses = len(result.scalars().fetchall())
                options.append(discord.SelectOption(
                    label=f'{member.name}',
                    description=f'Wins: {wins}, Loses: {loses}',
                    value=f'{member.id}'
                ))
            await session.close()

            view = PickView(captain, self.players, options)
            message = await interaction.channel.send(f'{captain.mention}', view=view)
            await view.wait()
            await message.delete()

            team.append(view.picked)
            self.players.remove(view.picked)

            _ = cap_embed(self.attackers, self.defenders, self.players)
            await interaction.edit_original_response(embed=_, view=self)
            turn = not turn

        # Access to vc
        self.vc1 = await interaction.channel.category.create_voice_channel(name=f'team_{self.attackers[0]}')
        self.vc2 = await interaction.channel.category.create_voice_channel(name=f'team_{self.defenders[0]}')
        await self.vc1.edit(sync_permissions=True)
        await self.vc2.edit(sync_permissions=True)

        for t, e in zip(self.attackers, self.defenders):
            await self.vc1.set_permissions(target=e, overwrite=discord.PermissionOverwrite(connect=False))
            await t.move_to(self.vc1)
            await self.vc2.set_permissions(target=t, overwrite=discord.PermissionOverwrite(connect=False))
            await e.move_to(self.vc2)

        if self.game.value == 'dota':
            alphabet = string.ascii_letters + string.digits
            lobby = f'discord.gg/5x5_{random.randint(0, 100)}'
            password = ''.join(secrets.choice(alphabet) for _ in range(6))
            await interaction.channel.send(embed=basic_embed(lobby, password))

        self.active_game = True
        await interaction.channel.send(f"Удачной игры!")

    @discord.ui.button(label='Завершить', style=discord.ButtonStyle.red)
    async def exit_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        """TODO: simplify way to add players"""
        if not self.active_game:
            await interaction.response.send_message(
                embed=basic_embed('Неактивная игра', 'Дождитесь окончания пика для завершения'), ephemeral=True)
            return

        view = WinnerView(self.attackers, self.defenders, self.game)
        await interaction.response.send_message(view=view, ephemeral=True)
        await view.wait()

        session = await create_session()
        result = await session.execute(select(Player).where(Player.id.in_(tuple([p.id for p in self.attackers]))))
        __attackers: list[Player] = result.scalars().fetchall()

        result = await session.execute(select(Player).where(Player.id.in_(tuple([p.id for p in self.defenders]))))
        __defenders: list[Player] = result.scalars().fetchall()

        lobby = Lobby(
            Teams.team1 if view.winner == self.attackers[0].id else Teams.team2,
            Games.dota if self.game.value == 'dota' else Games.valorant
        )

        for player in __attackers:
            a_table = PlayerClose(team=Teams.team1)
            a_table.player = player
            lobby.players.append(a_table)
            session.add(a_table)

        for player in __defenders:
            a_table = PlayerClose(team=Teams.team2)
            a_table.player = player
            lobby.players.append(a_table)
            session.add(a_table)

        await session.commit()
        await session.close()

        await interaction.channel.send('Завершено')
        await self.vc1.delete()
        await self.vc2.delete()
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator or settings.CLOSER_ROLE in interaction.user.roles:
            return True
        return False
