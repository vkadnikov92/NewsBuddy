import os
import csv
import json
import asyncio
from aiogram import Bot, Dispatcher, types
from telethon import TelegramClient
from datetime import datetime, timedelta
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from models.model_sibiryak import generate_summary

# Параметры Telethon
api_id = '25651742'
api_hash = 'e6947035583af4601a19198d41ed0b93'
phone = '+995592157452'
# client = TelegramClient(phone, api_id, api_hash)
client = TelegramClient('anon', api_id, api_hash)

# Параметры aiogram
API_TOKEN = '6370076869:AAGHr_0IK8hzwBmgbBr3FjNGkvvWa3R2BGI'
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# пустой файл будущей базы со связкой "пользователь <> его ссылки на каналы"
users_and_links_db = 'user_channels.json'
if not os.path.exists(users_and_links_db):
    with open(users_and_links_db, 'w') as f:
        json.dump({}, f)

@dp.message()
async def handle_message(message: types.Message):
    if message.text.startswith("/start") or message.text.startswith("/help"):
        await send_welcome(message)
    elif message.text.startswith("https://t.me/"):
        await save_channel_link(message)  # Сохраняем только ссылку
    elif message.text == "Саммари по моим источникам за вчера":
        await send_summary_to_user(message)
    elif message.text == "Рекомендации каналов":
        await send_recommendations(message)
    elif message.text == "Облако ключевых тем по моим каналам":
        await send_tags_cloud(message)
    elif message.text == "Посмотреть список моих каналов":
        await send_user_channels(message)
    # elif message.text == "Удалить неактуальные каналы":
    #     await show_channels_to_delete(message)
    elif message.text.startswith("удалить "):
        await remove_channel_by_number(message)
    else:
        await message.reply("Друг мой любезный, не пиши ерунды. Либо дай ссылку на канал новостной, либо гуляй себе с миром.")

# функция-приветствие и создание клавиатуры с командами
async def send_welcome(message: types.Message):
    kb = [
        [types.KeyboardButton(text="Посмотреть список моих каналов")],
        [types.KeyboardButton(text="Саммари по моим источникам за вчера")],
        [types.KeyboardButton(text="Рекомендации каналов")],
        [types.KeyboardButton(text="Облако ключевых тем по моим каналам")],
        # [types.KeyboardButton(text="Удалить неактуальные каналы")]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )
    await message.answer("Привет! Отправь мне ссылку на новостной канал вида 'https://t.me/', и я сохраню источник в своей базе.", reply_markup=keyboard)

# функция для отправки пользователю перечень его сохраненных каналов
async def send_user_channels(message: types.Message):
    user_id = str(message.from_user.id)
    with open(users_and_links_db, 'r') as f:
        data = json.load(f)
    user_channels = data.get(user_id, [])
    if user_channels:
        numbered_channels = "\n".join(f"{i}. {channel}" for i, channel in enumerate(user_channels, start=1))
        deletion_instruction = "\n\nЕсли вы хотите удалить какой-то из каналов, введите запрос в бот вида 'удалить 1, 4, 7', где цифры - номера каналов в списке выше."
        await message.reply(numbered_channels + deletion_instruction) # TODO убрать превью в выдаваемом сообщении
    else:
        await message.reply("У вас нет сохраненных каналов.")

# # функция удаления неактуальных более для польщователя каналов из базы
# async def show_channels_to_delete(message: types.Message):
#     user_id = str(message.from_user.id)
#     with open(users_and_links_db, 'r') as f:
#         data = json.load(f)
#     user_channels = data.get(user_id, [])
#     if not user_channels:
#         await message.reply("У вас нет сохраненных каналов.")
#         return
#     # Отправляем пользователю список его каналов и просим ввести номера тех, которые он хочет удалить
#     await message.reply("Введите номера каналов (в формате 'удалить 1, 3, 19'), которые вы хотите удалить, разделенные запятыми:\n" + "\n".join(f"{i}. {channel}" for i, channel in enumerate(user_channels, start=1)))

# функция для удаления выбранных пользователем каналов из базы
async def remove_channel_by_number(message: types.Message):
    user_id = str(message.from_user.id)
    channel_numbers_str = message.text.replace("удалить ", "")  # Удаляем "удалить " из строки
    
    with open(users_and_links_db, 'r') as f:
        data = json.load(f)
    user_channels = data.get(user_id, [])
    
    # Разделяем строку с номерами по запятой и удаляем пробелы
    channel_numbers_str_list = [num.strip() for num in channel_numbers_str.split(",")]
    
    # Проверяем, что все элементы в списке являются числами
    if all(num.isdigit() for num in channel_numbers_str_list):
        # Преобразуем строки в числа и уменьшаем их на 1, так как нумерация начинается с 1
        channel_numbers = [int(num) - 1 for num in channel_numbers_str_list]
        
        removed_channels = []
        # Удаляем каналы с указанными номерами
        for channel_number in sorted(channel_numbers, reverse=True):  # Удаляем с конца, чтобы избежать смещения индексов
            if 0 <= channel_number < len(user_channels):
                removed_channels.append(user_channels[channel_number])  # Добавляем удаленный канал в список
                del user_channels[channel_number]
            else:
                await message.answer(f"Неверный номер канала: {channel_number + 1}. Попробуйте еще раз.")
                return
        
        data[user_id] = user_channels
        with open(users_and_links_db, 'w') as f:
            json.dump(data, f)
        
        # Удаляем из news.csv новости, связанные с удаленными каналами
        try:
            with open('news.csv', 'r', newline='', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                remaining_news = [row for row in reader if not (row['channel_name'] in removed_channels and row['user_id'] == user_id)]
                # remaining_news = [row for row in reader if row['channel_name'] not in removed_channels or row['user_id'] != user_id]
        except FileNotFoundError:
            remaining_news = []
        
        with open('news.csv', 'w', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['user_id', 'channel_name', 'publication_text', 'publication_link', 'publication_date']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(remaining_news)

        await message.answer("Каналы и связанные с ними новости успешно удалены.")
    else:
        await message.answer("Пожалуйста, введите корректные номера каналов после слова 'удалить', разделенные запятыми.")

# функция для отправки рекомендация каналов пользователю на основании темактик присланных им каналов
async def send_recommendations(message: types.Message):
    await message.reply("Здесь будут рекомендации каналов.")

# функция для генерации облака тегов по новостям из каналов пользователя
async def send_tags_cloud(message: types.Message):
    await message.reply("Здесь будет облако ключевых тем.")

# Эта функция создает базу со связками сущностей "пользователь - каналы"
async def save_channel_link(message: types.Message):
    channel_link = message.text
    user_id = str(message.from_user.id)

    with open(users_and_links_db, 'r') as f:
        data = json.load(f)
    
    user_channels = data.get(user_id, [])
    if channel_link in user_channels:  # Если ссылка уже существует, удаляем ее
        user_channels.remove(channel_link)
    user_channels.append(channel_link)  # Добавляем ссылку в конец списка
    data[user_id] = user_channels
    
    with open(users_and_links_db, 'w') as f:
        json.dump(data, f)
    
    await message.reply("Новостая ссылка успешно сохранена в базу.", parse_mode='Markdown')

# функция-парсинга и сохранения новостей по заранее сохраненным ссылкам от пользователя
async def save_news(client, channel_link, user_id):
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    entity = await client.get_entity(channel_link)

    # Загрузка существующих новостей
    existing_news = []
    try:
        with open('news.csv', 'r', newline='', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if row['user_id'] == user_id:
                    existing_news.append(row['publication_link'])  # предполагается, что publication_link уникален для каждой новости
    except FileNotFoundError:
        pass  # Файл еще не создан

    async for msg in client.iter_messages(entity, limit=None): # Если хотим все вчерашние, то надо ставить limit=None
        msg_date = msg.date.replace(tzinfo=None)  # Убедитесь, что время в UTC
        if msg_date > twenty_four_hours_ago:
        # if msg_date.date() == yesterday.date():
            last_news = msg.text
            last_news_link = f"https://t.me/{channel_link.split('/')[-1]}/{msg.id}"
            
            # Проверка на уникальность новости перед сохранением
            if last_news_link not in existing_news:
                publication_text = msg.text.strip()  # Удаление пробелов с обеих сторон строки
                if publication_text:  # Проверка, что строка не пуста
                    with open('news.csv', 'a', newline='', encoding='utf-8') as csv_file:
                        fieldnames = ['user_id', 'channel_name', 'publication_text', 'publication_link', 'publication_date']
                        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                        if csv_file.tell() == 0:
                            writer.writeheader()
                        writer.writerow({
                            'user_id': user_id,
                            'channel_name': channel_link,
                            'publication_text': publication_text,
                            'publication_link': last_news_link,
                            'publication_date': msg_date.strftime('%Y-%m-%d %H:%M:%S')
                        })

async def send_summary_to_user(message: types.Message):
    user_id = str(message.from_user.id) # Уникальный идентификатор пользователя
    # Сначала собираем все сохраненные ссылки для этого пользователя
    with open(users_and_links_db, 'r') as f:
        data = json.load(f)
    channel_links = data.get(user_id, [])

    # Оставляем только 3 последних канала
    N = 3  # Количество последних каналов для саммаризации
    channel_links = channel_links[-N:]  # Оставляем только последние N каналов

    # Проверка на существование файла перед его открытием
    if not os.path.exists('news.csv'):
        with open('news.csv', 'w', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['user_id', 'channel_name', 'publication_text', 'publication_link', 'publication_date']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()  # Создание файла с заголовками, если файла не существует

    # Удаляем из news.csv все ранее собранные новости для этого пользователя
    try:
        with open('news.csv', 'r', newline='', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            remaining_news = [row for row in reader if row['user_id'] != user_id]
    except FileNotFoundError:
        remaining_news = []


    with open('news.csv', 'w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['user_id', 'channel_name', 'publication_text', 'publication_link', 'publication_date']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(remaining_news)

    # Обновляем news.csv, собирая новые новости по сохраненным ссылкам
    for channel_link in channel_links:
        await save_news(client, channel_link, user_id)  # Эта функция теперь просто сохраняет новости, не отправляя сообщений пользователю

    # После обновления news.csv генерируем сводку для всех новостей пользователя
    summary_list = []  # Список для хранения саммари

    with open('news.csv', 'r', newline='', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if row['user_id'] == str(user_id):  # Фильтрация по уникальному идентификатору пользователя
                publication_text = row['publication_text']
                publication_link = row['publication_link']
                summary = generate_summary(publication_text)  # Генерация саммари
                summary_with_link = f"{summary}\n[Link]({publication_link})" # Генерация саммари со ссылкой на источник
                summary_list.append(summary_with_link)
    if summary_list:
        summary_text = "\n\n---\n\n".join(summary_list)
        
        # Разбиваем длинное сообщение на части
        for i in range(0, len(summary_text), 4096):
            await message.reply(
                summary_text[i:i+4096],
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