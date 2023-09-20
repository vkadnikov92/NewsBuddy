import csv
import asyncio
from aiogram import Bot, Dispatcher, types
from telethon import TelegramClient
from datetime import datetime, timedelta

from models.model_sibiryak import generate_summary

# Параметры Telethon
api_id = 'X'
api_hash = 'X'
phone = '+X'
client = TelegramClient(phone, api_id, api_hash)

# Параметры aiogram
API_TOKEN = 'X'
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message()
async def handle_message(message: types.Message):
    if message.text.startswith("/start") or message.text.startswith("/help"):
        await send_welcome(message)
    elif message.text.startswith("https://t.me/"):
        await save_news(message)
    elif message.text.startswith("/getsummary"):
        await send_summary_to_user(message)
    else:
        await message.reply("Друг мой любезный, не пиши ерунды. Либо дай ссылку на канал новостной, либо гуляй себе с миром.")

async def send_welcome(message: types.Message):
    await message.reply("Привет! Отправь мне ссылку на новостной канал вида 'https://t.me/', и я сохраню источник в своей базе.")

async def save_news(message: types.Message):
    channel_link = message.text
    yesterday = datetime.utcnow() - timedelta(days=1)

    async with TelegramClient('anon', api_id, api_hash) as client:
        entity = await client.get_entity(channel_link)

        async for msg in client.iter_messages(entity, limit=20): # Если хотим все вчерашние, то надо ставить limit=None
            msg_date = msg.date.replace(tzinfo=None)  # Убедитесь, что время в UTC

            if msg_date.date() == yesterday.date():
                last_news = msg.text
                last_news_link = f"https://t.me/{channel_link.split('/')[-1]}/{msg.id}"

                with open('news.csv', 'a', newline='', encoding='utf-8') as csv_file:
                    fieldnames = ['user_id', 'channel_name', 'publication_text', 'publication_link', 'publication_date']
                    # fieldnames = ['channel_name', 'publication_text', 'publication_link']
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                    if csv_file.tell() == 0:
                        writer.writeheader()
                    writer.writerow({
                        'user_id': message.from_user.id,
                        'channel_name': channel_link,
                        'publication_text': last_news,
                        'publication_link': last_news_link,
                        'publication_date': msg_date.strftime('%Y-%m-%d %H:%M:%S')  # Форматируем дату
                    })

        await message.reply("Сохранение новостей за вчерашний день завершено.", parse_mode='Markdown')
        # await message.reply(f"Последняя новость из {channel_link}:\n\n{last_news}\n\n[Ссылка на новость]({last_news_link})", parse_mode='Markdown')

async def send_summary_to_user(message: types.Message):
    user_id = message.from_user.id  # Уникальный идентификатор пользователя
    yesterday = datetime.utcnow() - timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')  # Форматируем дату в строку для сравнения

    summary_list = []  # Список для хранения саммари

    with open('news.csv', 'r', newline='', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if row['user_id'] == str(user_id):  # Фильтрация по уникальному идентификатору пользователя
                publication_date = datetime.strptime(row['publication_date'], '%Y-%m-%d %H:%M:%S')
                publication_date_str = publication_date.strftime('%Y-%m-%d')

                if publication_date_str == yesterday_str:  # Проверка, что новость от вчерашнего дня
                    publication_text = row['publication_text']
                    summary = generate_summary(publication_text)  # Генерация саммари
                    summary_list.append(summary)
    summary_list = [s.replace("<extraid0>", "").strip() for s in summary_list]
    if summary_list:
        summary_text = "\n\n".join(summary_list)
        await message.reply(
            f"Вчерашние новости в саммари:\n\n{summary_text}",
            parse_mode='Markdown'
        )
    else:
        await message.reply(
            "Нет новостей за вчерашний день.",
            parse_mode='Markdown'
        )

async def start_client_and_polling():
    await client.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_client_and_polling())