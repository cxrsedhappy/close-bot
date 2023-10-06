import random
import string
import secrets
import discord
import settings

from discord import Member
from discord.app_commands import Choice

from views.pick import Pick
from views.menu import WinnerView

from sqlalchemy import select
from data.db_session import Lobby, Player, PlayerClose, create_session, Teams, Games


class CaptainsView(discord.ui.View):
    def __init__(self, attackers: list[Member], defenders: list[Member], players: list[Member], game: Choice):
        super().__init__()
        self._players = players
        self._game = game

        self._attackers = attackers
        self._defenders = defenders

        self._vc1 = None
        self._vc2 = None
        self._active_game = False

        self.timeout = 60 * 60 * 5  # 5 hours

    async def embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="Выбор игроков",
            description=f'**Капитаны**: {self._attackers[0].mention} и {self._defenders[0].mention}',
            colour=2829617
        )
        msg = '\n'.join(player.mention for player in self._players)
        t1 = '\n'.join(player.mention for player in self._attackers)
        t2 = '\n'.join(player.mention for player in self._defenders)

        if msg != '':
            embed.add_field(name='Игроки', value=msg)

        cap1 = await Player.get_player(self._attackers[0].id)
        cap2 = await Player.get_player(self._defenders[0].id)
        embed.add_field(name=f'{cap1.lobby_nickname}', value=t1)
        embed.add_field(name=f'{cap2.lobby_nickname}', value=t2)
        return embed

    @discord.ui.button(label='Начать', style=discord.ButtonStyle.green)
    async def registration_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        button.disabled = True
        await interaction.edit_original_response(view=self)

        turn = False
        teams = (self._attackers, self._defenders)

        n = len(self._players)
        for i in range(n):
            captain: discord.Member = teams[turn][0]
            team: list[discord.Member] = teams[turn]

            # Filling options (Temporary solution)
            # Better create class LobbyPlayer with user and stats to reduce database usage
            options = []
            async with create_session() as session:
                async with session.begin():
                    for member in self._players:
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

            view = Pick(captain, self._players, options)
            message = await interaction.channel.send(f'{captain.mention}', view=view)
            await view.wait()
            await message.delete()

            team.append(view.picked)
            self._players.remove(view.picked)

            await interaction.edit_original_response(embed=await self.embed(), view=self)
            turn = not turn

        # Access to vc
        cap_1 = await Player.get_player(self._attackers[0].id)
        cap_2 = await Player.get_player(self._defenders[0].id)
        self._vc1 = await interaction.channel.category.create_voice_channel(name=f'{cap_1.lobby_nickname}')
        self._vc2 = await interaction.channel.category.create_voice_channel(name=f'{cap_2.lobby_nickname}')
        await self._vc1.edit(sync_permissions=True)
        await self._vc2.edit(sync_permissions=True)

        for t, e in zip(self._attackers, self._defenders):
            await self._vc1.set_permissions(target=e, overwrite=discord.PermissionOverwrite(connect=False))
            await self._vc2.set_permissions(target=t, overwrite=discord.PermissionOverwrite(connect=False))

        if self._game.value == 'dota':
            lobby = f'discord.gg/fivexfive-close-{random.randint(0, 100)}'
            password = ''.join(secrets.choice(string.digits) for _ in range(6))
            await interaction.channel.send(embed=discord.Embed(title=lobby, description=password, colour=2829617))

        self._active_game = True
        await interaction.channel.send('Перейдите в каналы ваших команд\nУдачной игры!')

    @discord.ui.button(label='Завершить', style=discord.ButtonStyle.red)
    async def exit_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._active_game:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title='Неактивная игра',
                    description='Дождитесь окончания пика для завершения',
                    colour=2829617),
                ephemeral=True
            )
            return

        # Can't use await Player.get_player() inside sync function
        cap1 = await Player.get_player(self._attackers[0].id)
        cap2 = await Player.get_player(self._defenders[0].id)

        options = [
            discord.SelectOption(label=f'{cap1.lobby_nickname}', value=f'{self._attackers[0].id}'),
            discord.SelectOption(label=f'{cap2.lobby_nickname}', value=f'{self._defenders[0].id}'),
        ]

        view = WinnerView(self._attackers, self._defenders, options, self._game)
        await interaction.response.send_message(view=view, ephemeral=True)
        await view.wait()

        async with create_session() as session:
            async with session.begin():
                result = await session.execute(
                    select(Player).where(Player.id.in_(tuple([p.id for p in self._attackers]))))
                _attackers: list[Player] = result.scalars().fetchall()

                result = await session.execute(
                    select(Player).where(Player.id.in_(tuple([p.id for p in self._defenders]))))
                _defenders: list[Player] = result.scalars().fetchall()

                lobby = Lobby(
                    Teams.team1 if view.winner_id == self._attackers[0].id else Teams.team2,
                    Games.dota if self._game.value == 'dota' else Games.valorant
                )

                _attackers[0].coins += 100 if view.winner_id == self._attackers[0].id else 0
                _defenders[0].coins += 100 if view.winner_id == self._defenders[0].id else 0

                # Simplify this
                for player in _attackers:
                    a_table = PlayerClose(team=Teams.team1)
                    player.is_registered = False
                    player.coins += 250 if lobby.winner == Teams.team1 else 125
                    a_table.player = player
                    lobby.players.append(a_table)
                    session.add(a_table)

                for player in _defenders:
                    a_table = PlayerClose(team=Teams.team2)
                    player.is_registered = False
                    player.coins += 250 if lobby.winner == Teams.team2 else 125
                    a_table.player = player
                    lobby.players.append(a_table)
                    session.add(a_table)

        await interaction.channel.send('Завершено')
        await self._vc1.delete()
        await self._vc2.delete()
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator or settings.CLOSER_ROLE in interaction.user.roles:
            return True
        return False
