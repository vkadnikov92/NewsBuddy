import os
import csv
import json
import asyncio
from aiogram import Bot, Dispatcher, types
from telethon import TelegramClient
from datetime import datetime, timedelta
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, BufferedInputFile
import io
import random
from config import API_ID, API_HASH, API_TOKEN, PHONE
from models.model_sibiryak import generate_summary
from models.news_to_cloud import generate_word_cloud_image
from models.recsys_ml import generate_recommendations
from quotes_categories import QUOTES
from quotes_categories import category_to_channels
import time

# Параметры Telethon
api_id = API_ID
api_hash = API_HASH
phone = PHONE
client = TelegramClient('anon', api_id, api_hash)

# Параметры aiogram
API_TOKEN = API_TOKEN
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# CONSTS
USERS_AND_LINKS_DB = 'user_channels.json'
NEWS_CSV_PATH = 'news.csv'

# пустой файл будущей базы со связкой "пользователь <> его ссылки на каналы"
if not os.path.exists(USERS_AND_LINKS_DB):
    with open(USERS_AND_LINKS_DB, 'w') as f:
        json.dump({}, f)

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


# функция для отправки смешной цитаты преподавателей
async def send_quote(message: types.Message):
    quote = random.choice(QUOTES)
    await message.reply(quote)


# функция для отправки пользователю перечень его сохраненных каналов
async def send_user_channels(message: types.Message):
    user_id = str(message.from_user.id)
    with open(USERS_AND_LINKS_DB, 'r') as f:
        data = json.load(f)
    user_channels = data.get(user_id, [])
    if user_channels:
        numbered_channels = "\n".join(f"{i}. {channel}" for i, channel in enumerate(user_channels, start=1))
        deletion_instruction = "\n\nЕсли вы хотите удалить какой-то из каналов, введите запрос в бот команду вида 'удалить 1, 4, 12', где числа - номера каналов в списке выше."
        await message.reply(numbered_channels + deletion_instruction) # TODO убрать превью в выдаваемом сообщении
    else:
        await message.reply("У вас нет сохраненных каналов.")

# функция для удаления выбранных пользователем каналов из базы
async def remove_channel_by_number(message: types.Message):
    user_id = str(message.from_user.id)
    channel_numbers_str = message.text.replace("удалить ", "")  # Удаляем "удалить " из строки
    
    with open(USERS_AND_LINKS_DB, 'r') as f:
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
        with open(USERS_AND_LINKS_DB, 'w') as f:
            json.dump(data, f)
        
        # Удаляем из news.csv новости, связанные с удаленными каналами
        try:
            with open('news.csv', 'r', newline='', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                remaining_news = [row for row in reader if not (row['channel_name'] in removed_channels and row['user_id'] == user_id)]
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

# Эта функция создает базу со связками сущностей "пользователь - каналы"
async def save_channel_link(message: types.Message):
    channel_link = message.text
    user_id = str(message.from_user.id)

    with open(USERS_AND_LINKS_DB, 'r') as f:
        data = json.load(f)
    
    user_channels = data.get(user_id, [])
    if channel_link in user_channels:  # Если ссылка уже существует, удаляем ее
        user_channels.remove(channel_link)
    user_channels.append(channel_link)  # Добавляем ссылку в конец списка
    data[user_id] = user_channels
    
    with open(USERS_AND_LINKS_DB, 'w') as f:
        json.dump(data, f)
    
    await message.reply("Новостая ссылка успешно сохранена в базу.", parse_mode='Markdown')

# новая функция сохранения новостей
# N_channels - ограничение числа каналов из списка пользователя, по которым будет парсить
# news_limit_per_channel - ограничение числа новостей в каждом канала списка пользователя для парсинга
async def save_news(client, user_id, N_channels=3, news_limit_per_channel=10):
    start_time = time.time()
    print(f"Start saving news for user_id {user_id}")
    
    # Получаем список каналов пользователя
    with open('user_channels.json', 'r') as f:
        user_channels = json.load(f).get(str(user_id), [])[-N_channels:]
    
    new_rows = []
    for channel_link in user_channels:
        entity = await client.get_entity(channel_link)
        async for msg in client.iter_messages(entity, limit=news_limit_per_channel):
            msg_date = msg.date.replace(tzinfo=None)
            last_news_link = f"https://t.me/{channel_link.split('/')[-1]}/{msg.id}"
            publication_text = msg.text.strip() if msg.text else ""
            if publication_text:
                new_rows.append({
                    'user_id': user_id,
                    'channel_name': channel_link,
                    'publication_text': publication_text,
                    'publication_link': last_news_link,
                    'publication_date': msg_date.strftime('%Y-%m-%d %H:%M:%S')
                })
    
    with open('news.csv', 'a', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['user_id', 'channel_name', 'publication_text', 'publication_link', 'publication_date']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writerows(new_rows)
    print("Time taken for writing to CSV: %s seconds" % (time.time() - start_time))


# функция обновления news.csv - удаляет старые новости, парсит новые с помощью другой функции save_news
# N_channels - ограничение числа каналов из списка пользователя, по которым будет парсить
async def update_news_csv(user_id, N_channels=5):
    start_time = time.time()
    print(f"Updating news.csv for user_id {user_id}")

    # Проверка на существование файла перед его открытием
    if os.path.exists('news.csv'):
        # Если файл существует, удаляем старые новости пользователя
        with open('news.csv', 'r', newline='', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            remaining_news = [row for row in reader if row['user_id'] != str(user_id)]
    else:
        # Если файла не существует, то просто создаем пустой список
        remaining_news = []
        # и создаем файл с заголовками
        with open('news.csv', 'w', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['user_id', 'channel_name', 'publication_text', 'publication_link', 'publication_date']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()  # Создание файла с заголовками, если файла не существует

    # Запись обновленных данных обратно в файл
    with open('news.csv', 'w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['user_id', 'channel_name', 'publication_text', 'publication_link', 'publication_date']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        if not remaining_news:  # Если список пуст, то записываем заголовки
            writer.writeheader()
        writer.writerows(remaining_news)
    
    await save_news(client, user_id, N_channels=N_channels)
    print("Time taken for update_news_csv: %s seconds" % (time.time() - start_time))

# функция для отправки рекомендация каналов пользователю на основании темактик присланных им каналов
async def send_recommendations(message: types.Message):
    start_time = time.time() # отладка
    user_id = str(message.from_user.id)
    await update_news_csv(user_id, 5)  # Обновляем news.csv перед генерацией облака тегов по 5 каналам пользователя
    user_id = int(user_id)
    print("Time taken for update_news_csv: %s seconds" % (time.time() - start_time)) # отладка
    start_time = time.time()  # Resetting start_time # отладка
    

    recommended_channels = generate_recommendations(user_id, NEWS_CSV_PATH, category_to_channels)
    print("Time taken for generate_recommendations: %s seconds" % (time.time() - start_time)) # отладка
    start_time = time.time()  # Resetting start_time # отладка

    if not recommended_channels:
        print("No recommendations found for user_id:", user_id)
    if recommended_channels:
        recommended_channels_str = "\n".join(recommended_channels)
        await message.reply(f"Вот несколько рекомендованных каналов для вас:\n{recommended_channels_str}")
    else:
        await message.reply("Извините, но мы не смогли найти подходящих рекомендаций для вас.")
    print("Time taken for sending message: %s seconds" % (time.time() - start_time)) # отладка

# функция для генерации облака тегов по новостям из каналов пользователя
async def send_tags_cloud(message: types.Message):
    start_time = time.time() # отладка
    user_id = str(message.from_user.id)
    await update_news_csv(user_id, 5)  # Обновляем news.csv перед генерацией облака тегов по 5 каналам пользователя
    
    print("Time taken for update_news_csv: %s seconds" % (time.time() - start_time)) # отладка
    start_time = time.time()  # Resetting start_time

    try:
        img = generate_word_cloud_image('news.csv', user_id)
        print("Time taken for generate_word_cloud_image: %s seconds" % (time.time() - start_time)) # отладка
        start_time = time.time()  # Resetting start_time # отладка

        if img:
            buffer = io.BytesIO(img.getvalue())  # Создайте буфер
            buffer.seek(0)  # Переместите курсор обратно к началу файла
            await bot.send_photo(chat_id=message.chat.id, photo=BufferedInputFile(buffer.read(), filename="cloud.png"), caption="Облако ключевых тем")
        else:
            await message.reply("Нет новостей за последние 24 часа.")
        print("Time taken for sending message or image: %s seconds" % (time.time() - start_time))
    except Exception as e:
        await message.reply(f"Произошла ошибка: {str(e)}")

# функция отправки саммари новостей пользователю
async def send_summary_to_user(message: types.Message):   
    # Отправляем пользователю сообщение о том, что ему нужно подождать
    # await message.reply("Пожалуйста, подождите, это может занять некоторое время, если новостей в каналах и самих каналов много. \n" # не работает
    #                     "Пока вы ждете, узнайте мудрость восходителей по кнопке \n'🏔️ Цитаты великих восходителей Эльбруса'")

    user_id = str(message.from_user.id) # Уникальный идентификатор пользователя
    await update_news_csv(user_id, 3)  # Обновляем news.csv перед генерацией сводки по 3 каналам пользователя
    
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