import os
from dotenv import load_dotenv

load_dotenv()


class Prod:
    app_id = os.getenv('APP_ID')
    token = os.getenv('TOKEN')
    server = 1078646667533889550
    registration = 1145771495373680761
    history = 1156303654186401823
    closer = 1112507783993106433
    private_rooms_category = 1153441782953160795
    manage = 1153441934128467968
    entry_room = 1153441991980494879


class Test:
    app_id = os.getenv('TEST_APP_ID')
    token = os.getenv('TEST_TOKEN')
    server = 974988972864471061
    registration = 1159916354363732050
    history = 1159916483246309459
    closer = 1159916541748457482
    private_rooms_category = 974988973317447771
    manage = 1160200051893751830
    entry_room = 1160212025083961465


mode = Prod

APP_ID = mode.app_id
TOKEN = mode.token

SERVER = mode.server
REG_CATEGORY_ID = mode.registration
HISTORY_CHANNEL_ID = mode.history
CLOSER_ROLE = mode.closer

PRIVATE_ROOMS_CATEGORY_ID = mode.private_rooms_category
MANAGE_CHANNEL_ID = mode.manage
ENTRY_ROOM_ID = mode.entry_room
