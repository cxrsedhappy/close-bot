import os

from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv('TEST_APP_ID')
TOKEN = os.getenv('TEST_TOKEN')


class Prod:
    server = 1078646667533889550
    registration = 1145771495373680761
    history = 1156303654186401823
    closer = 1112507783993106433


class Test:
    server = 974988972864471061
    registration = 1159916354363732050
    history = 1159916483246309459
    closer = 1159916541748457482


mode = Test

SERVER = mode.server
REG_CATEGORY_ID = mode.registration
HISTORY_CHANNEL_ID = mode.history
CLOSER_ROLE = mode.closer