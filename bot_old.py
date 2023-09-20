import csv
import asyncio
from aiogram import Bot, Dispatcher, types, Router
from telethon import TelegramClient
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from model import summery_gen


# Параметры Telethon
api_id = 'X'
api_hash = 'X'
phone = '+X'
client = TelegramClient(phone, api_id, api_hash)

# Параметры aiogram
API_TOKEN = 'X:X'
bot = Bot(token=API_TOKEN)
# router = Router()
dp = Dispatcher()

@dp.message()
# @router.message()
async def handle_message(message: types.Message):
    if message.text.startswith("/start") or message.text.startswith("/help"):
        await send_welcome(message)
    elif message.text.startswith("https://t.me/"):
        await fetch_last_news(message)
    elif message.text.startswith("/getsummary"):
        await send_summary_to_user(message)
    else:
        await message.reply("Друг мой любезный, не пиши ерунды. Либо дай ссылку на канал новостной, либо гуляй себе с миром.")

async def send_welcome(message: types.Message):
    # markup = InlineKeyboardMarkup()
    # markup.add(InlineKeyboardButton("Получить последние новости", callback_data="fetch_last_news"))
    # markup.add(InlineKeyboardButton("Получить саммари", callback_data="get_summary"))

    # welcome_text = (
    #     f"Привет! Отправь мне ссылку на новостной канал вида 'https://t.me/', "
    #     f"и я верну последнюю новость оттуда. "
    #     f"После отправки ссылки ты сможешь выбрать действие ниже:"
    # )

    # await message.reply(welcome_text, reply_markup=markup)
    await message.reply(f"Привет! Отправь мне ссылку на новостной канал вида 'https://t.me/', и я верну последнюю новость оттуда.")

# @router.callback_query()
# async def callback_query_handler(callback_query: types.CallbackQuery):
#     if callback_query.data == 'fetch_last_news':
#         await fetch_last_news(callback_query.message)
#     elif callback_query.data == 'get_summary':
#         await send_summary_to_user(callback_query.message)


async def fetch_last_news(message: types.Message):
    user_id = message.from_user.id  # Уникальный идентификатор пользователя
    channel_link = message.text
    yesterday = datetime.utcnow() - timedelta(days=1) # берем последние сутки, получается

    async with TelegramClient('anon', api_id, api_hash) as client:
        entity = await client.get_entity(channel_link)

        async for msg in client.iter_messages(entity, limit=20): #  по идее None нужен, чтобы весь вчерашний день смотреть
            msg_date = msg.date.replace(tzinfo=None)  # Убедитесь, что время в UTC

            if msg_date.date() == yesterday.date():
                last_news = msg.text
                summary = summery_gen(msg.text)
                last_news_link = f"https://t.me/{channel_link.split('/')[-1]}/{msg.id}"
                
                with open('news.csv', 'a', newline='', encoding='utf-8') as csv_file:
                    fieldnames = ['user_id', 'channel_name', 'publication_text', 'publication_link', 'publication_date']
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                    
                    # Проверка, пустой ли файл, чтобы не перезаписывать заголовки
                    if csv_file.tell() == 0:
                        writer.writeheader()  # Запись заголовков в CSV-файл
                    
                    writer.writerow({
                        'user_id': user_id,
                        'channel_name': channel_link,
                        'publication_text': last_news,
                        'publication_link': last_news_link,
                        'publication_date': msg_date.strftime('%Y-%m-%d %H:%M:%S')  # Форматируем дату
                    })

        await message.reply(
            f"Сохранение новостей за вчерашний день завершено.\n\n"
            f"Последняя новость из {channel_link}:\n\n{last_news}\n\n"
            f"[Ссылка на новость]({last_news_link})\n"
            f"Коротко саммари новости: \n{summary}",
            parse_mode='Markdown')

async def send_summary_to_user(message: types.Message):
    user_id = message.from_user.id  # Уникальный идентификатор пользователя
    yesterday = datetime.now() - timedelta(days=1)
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
                    summary = summery_gen(publication_text)  # Генерация саммари
                    summary_list.append(summary)

    if summary_list:
        summary_text = "\n".join(summary_list)
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

