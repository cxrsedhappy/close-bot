import secrets
import string
import random

alphabet = string.ascii_letters + string.digits
lobby = f'discord.gg/5x5_dota2-{random.randint(0, 100)}'
password = ''.join(secrets.choice(alphabet) for _ in range(12))

print(lobby, password)
