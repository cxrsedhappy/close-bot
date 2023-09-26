from discord import Embed, Member
from discord.app_commands import Choice

base_url = f'https://cdn.discordapp.com/attachments/1147246596170448896'

thumbnails = {
    10: f'{base_url}/1148019117559910430/full.png',
    9: f'{base_url}/1148019096148000768/1.png',
    8: f'{base_url}/1148019096437399662/2.png',
    7: f'{base_url}/1148019096789725204/3.png',
    6: f'{base_url}/1148019097255297045/4.png',
    5: f'{base_url}/1148019097624387584/5.png',
    4: f'{base_url}/1148019097863467188/6.png',
    3: f'{base_url}/1148019098375168151/7.png',
    2: f'{base_url}/1148019098714910751/8.png',
    1: f'{base_url}/1148019099012710471/9.png',
    0: f'{base_url}/1148019095841812590/10.png'
}

games = {
    'dota': f'{base_url}/1147574166376169652/dota2close.png',
    'valorant': f'{base_url}/1147574166636200057/valorantclose.png'
}


def basic_embed(title: str = '', description: str = '', colour=2829617) -> Embed:
    return Embed(title=title, description=description, colour=colour)


def reg_embed(players: list[Member], game: Choice) -> Embed:
    description = ''
    for i, player in enumerate(players, start=1):
        description += f'{i}: {player.mention}\n'

    embed = basic_embed(f'Игроки ({len(players)} из 10)', description)
    embed.set_thumbnail(url=thumbnails.get(len(players), 0))
    embed.set_image(url=games.get(game.value))
    embed.set_author(name=f"Регистрация на Close по {game.name}")

    return embed


def cap_embed(team1: list[Member], team2: list[Member], remaining: list[Member]) -> Embed:
    embed = basic_embed("Выбор игроков", f'**Капитаны**: {team1[0].mention} и {team2[0].mention}')
    msg = '\n'.join(player.mention for player in remaining)
    t1 = '\n'.join(player.mention for player in team1)
    t2 = '\n'.join(player.mention for player in team2)

    if msg != '':
        embed.add_field(name='Игроки', value=msg)

    embed.add_field(name=f'team_{team1[0].name}', value=t1)
    embed.add_field(name=f'team_{team2[0].name}', value=t2)

    return embed
