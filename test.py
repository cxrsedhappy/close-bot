from data.members import Player, Close, PlayerClose, Teams
from data.db_session import global_init, create_session

global_init('db/database')
connection = create_session()

player = connection.query(Player).limit(10).all()

team_player = player[:5]
enemy_players = player[5:]

print(team_player)
print(enemy_players)

# c = Close(winner=Teams.team1)

# for p in team_player:
#     a = PlayerClose(team=Teams.team1)
#     a.close = c
#     p.closes.append(a)
#     connection.add(a)
#
# for p in enemy_players:
#     a = PlayerClose(team=Teams.team2)
#     a.close = c
#     p.closes.append(a)
#     connection.add(a)

"TODO: Learn SQLAlchemy to make better requests"
for p in team_player:
    print(p.id, p.coins, p.closes)

connection.close()



