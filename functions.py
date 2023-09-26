import os
import json
import csv
import random
from aiogram import types
from datetime import datetime, timedelta
from models.model_sibiryak import generate_summary
from models.news_to_cloud import generate_word_cloud_image
from models.recsys_ml import generate_recommendations, category_to_channels
from quotes import QUOTES
from client import client, bot
import io
from aiogram.types import BufferedInputFile

# CONSTS
USERS_AND_LINKS_DB = 'user_channels.json'
NEWS_CSV_PATH = 'news.csv'

# пустой файл будущей базы со связкой "пользователь <> его ссылки на каналы"
if not os.path.exists(USERS_AND_LINKS_DB):
    with open(USERS_AND_LINKS_DB, 'w') as f:
        json.dump({}, f)


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
            # last_news = msg.text
            last_news_link = f"https://t.me/{channel_link.split('/')[-1]}/{msg.id}"
            
            # Проверка на уникальность новости перед сохранением
            if last_news_link not in existing_news:
                publication_text = msg.text.strip() if msg.text else ""  # Удаление пробелов с обеих сторон строки, если msg.text не None
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


# функция по обновлению news.csv - удаляет старые новости, парсит новые
# N - ограничение числа каналов из списка пользователя, по которым будет парсить 
async def update_news_csv(user_id, N):
    # Сначала собираем все сохраненные ссылки для этого пользователя
    with open(USERS_AND_LINKS_DB, 'r') as f:
        data = json.load(f)
    channel_links = data.get(user_id, [])
    channel_links = channel_links[-N:]  # Оставляем только последние N каналов

    fieldnames = ['user_id', 'channel_name', 'publication_text', 'publication_link', 'publication_date']
    
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

    # Запись обновленных данных обратно в файл
    with open('news.csv', 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(remaining_news)

    # Обновляем news.csv, собирая новые новости по сохраненным ссылкам
    for channel_link in channel_links:
        await save_news(client, channel_link, user_id)  # Эта функция сохраняет новости, не отправляя сообщений пользователю


# функция для отправки рекомендация каналов пользователю на основании темактик присланных им каналов
async def send_recommendations(message: types.Message):
    user_id = int(message.from_user.id)
    await update_news_csv(user_id, 5)  # Обновляем news.csv перед генерацией облака тегов по 5 каналам пользователя

    recommended_channels = generate_recommendations(user_id, NEWS_CSV_PATH, category_to_channels)
    if not recommended_channels:
        print("No recommendations found for user_id:", user_id)
    if recommended_channels:
        recommended_channels_str = "\n".join(recommended_channels)
        await message.reply(f"Вот несколько рекомендованных каналов для вас:\n{recommended_channels_str}")
    else:
        await message.reply("Извините, но мы не смогли найти подходящих рекомендаций для вас.")
    # await message.reply("Здесь будут рекомендации каналов.") TODO delete


# функция для генерации облака тегов по новостям из каналов пользователя
async def send_tags_cloud(message: types.Message):
    user_id = str(message.from_user.id)
    await update_news_csv(user_id, 5)  # Обновляем news.csv перед генерацией облака тегов по 5 каналам пользователя
    
    try:
        img = generate_word_cloud_image('news.csv', user_id)
        if img:
            buffer = io.BytesIO(img.getvalue())  # Создайте буфер
            buffer.seek(0)  # Переместите курсор обратно к началу файла
            await bot.send_photo(chat_id=message.chat.id, photo=BufferedInputFile(buffer.read(), filename="cloud.png"), caption="Облако ключевых тем")
        else:
            await message.reply("Нет новостей за последние 24 часа.")
    except Exception as e:
        await message.reply(f"Произошла ошибка: {str(e)}")

# функция отправки саммари новостей пользователю
async def send_summary_to_user(message: types.Message):
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
