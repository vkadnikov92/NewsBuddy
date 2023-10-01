# NewsBuddy

<p align="center">
  <img src="img/main.png" width="400">
</p>

**NewsBuddy** - это бот, который поможет вам фокусироваться только на важной и интересной информации.    

Бот соберёт публикации с тех каналов, которые вы укажете и даст вам краткое изложение за день. Вы сможете ознакомится с ключевыми мыслями публикаций или перейти к их полным версиям, если вас заинтересовало что-то конкретное. 

<p float="left">
  <img src="img/summary.png" />
  <img src="img/full_news.png" /> 
</p>

**NewsBuddy** умеет рекомендовать вам каналы в зависимости от ваших предпочтений и интересов. 
![image](img/recsys.png)

А ещё, **NewsBuddy** может провести морфологический анализ публикаций из интересных вам телеграм-каналов и создать **облако слов**.
![image](img/cloud.png)


# Команда проекта
1. [Владимир Кадников](https://github.com/vkadnikov92)
2. [Григорий Ржищев](https://github.com/Rzhischev)
3. [Владислав Филиппов](https://github.com/Vlad1slawoo)
   
# Библиотеки
```typescript
import os
import io
import csv
import time
import json
import random
import asyncio
from aiogram import Bot, Dispatcher, types
from telethon import TelegramClient
from datetime import datetime, timedelta
from aiogram.types import BufferedInputFile
```
# Установка 
1. Перейдите в директорию в которой хотите хранить репозиторий с ботом
2. Клониройте репозиторий на ваш пк(git clone git@github.com:vkadnikov92/NewsBuddy.git)
# Запуск 
1. Перейдите на [сайт](https://my.telegram.org/auth) и создайте свое приложение, оно понадобится для работы бота
2. Создайте своего бота в BotFather telegram 
3. Перейдите в директорию с ботом и активируйте свое виртуальное окружение для данного проекта
4. Установите необходимые библиотеки из requirements.txt(pip install -r requirements.txt)
5. Заполните необхходимые поля(api_id api_hash phone и API_TOKEN) в файле bot.py (данные должны быть у вас после 1 и 2 шагов)
6. После заполнения необходимых переменных просто запустите bot.py и пройдите аутентификацию используя ваш номер телефона в телеграм(не работает при включенной двухфакторной аутентификации)
# Использование 
Теперь, когда бот установлен и запущен вы можете пользоваться его основными функциями:
1. Заправшивать у него саммари телеграм-каналов, которые вы ему отправили
2. Получать рекомендации по каналам в зависимости от ваших интересов
3. Генерировать облако слов по вашим источникам
4. Читать цитаты лучших из Elbrus Bootcamp

# Стек
![aiogram](https://img.shields.io/badge/aiogram-Used-blue)
![pytorch](https://img.shields.io/badge/pytorch-Used-yellow)
![telethon](https://img.shields.io/badge/telethon-Used-green)
![sklearn](https://img.shields.io/badge/sklearn-Used-orange)
![huggingface](https://img.shields.io/badge/huggingface-Used-purple)

