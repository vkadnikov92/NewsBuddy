from telethon import TelegramClient
from config import API_ID, API_HASH, API_TOKEN
from aiogram import Bot, Dispatcher

# Telethon
client = TelegramClient('anon', API_ID, API_HASH)

# Параметры aiogram
API_TOKEN = API_TOKEN
bot = Bot(token=API_TOKEN)