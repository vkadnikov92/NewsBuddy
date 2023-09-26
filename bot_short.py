import asyncio
from aiogram import Bot, Dispatcher, types
from telethon import TelegramClient
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, BufferedInputFile
from client import client, bot
from config import API_TOKEN
from functions import save_channel_link, send_summary_to_user, send_recommendations, send_tags_cloud, send_user_channels, remove_channel_by_number, send_quote


bot = bot
dp = Dispatcher()


@dp.message()
async def handle_message(message: types.Message):
    if message.text.startswith("/start") or message.text.startswith("/help"):
        await send_welcome(message)
    elif message.text.startswith("https://t.me/"):
        await save_channel_link(message) 
    elif message.text == "📰 Саммари моих новостей за 24ч":
        await send_summary_to_user(message)
    elif message.text == "🌟 Рекомендации каналов":
        await send_recommendations(message)
    elif message.text == "☁️ Облако ключевых тем по моим новостям":
        await send_tags_cloud(message)
    elif message.text == "📚 Мои источники":
        await send_user_channels(message)
    elif message.text.startswith("удалить "):
        await remove_channel_by_number(message)
    elif message.text == "🏔️ Цитаты великих восходителей Эльбруса":
        await send_quote(message)
    else:
        await message.reply("Друг мой любезный, не плоди лишней информации - ее и так слишком много в этом мире. Дай ссылку на новостной канал или пользуйся командами ниже.")

# функция-приветствие и создание клавиатуры с командами
async def send_welcome(message: types.Message):
    kb = [
        [types.KeyboardButton(text="📚 Мои источники"), types.KeyboardButton(text="🌟 Рекомендации каналов")],
        [types.KeyboardButton(text="📰 Саммари моих новостей за 24ч")],
        [types.KeyboardButton(text="☁️ Облако ключевых тем по моим новостям")],
        [types.KeyboardButton(text="🏔️ Цитаты великих восходителей Эльбруса")],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,

        resize_keyboard=True,
        input_field_placeholder="Выберите действие или отправьте ссылку на канал'"
    )
    await message.answer("Привет! Я твой NewsBuddy - бот, помогающий собрать актуальные новости в одном месте.\n\n"
                         "Отправь мне ссылку на телеграм канал вида 'https://t.me/', и я сохраню его в своей базе, чтобы потом делиться с тобой новостной картиной дня.\n\n"
                         "Я еще в начальной фазе разработки, поэтому умерь свои ожидания :)", reply_markup=keyboard)


async def start_client_and_polling():
    await client.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_client_and_polling())