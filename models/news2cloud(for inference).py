# ВЫТАСКИВАЕМ НОВОСТИ ПО ПОЛЬЗОВАТЕЛЮ ЗА ПОСЛЕДНИЕ 24 ЧАСА"

import csv
from datetime import datetime, timedelta


def get_news(csv_file, user_id):
    try:
        # Открываем CSV файл для чтения
        with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Определяем текущую дату и время
            current_datetime = datetime.now()
            
            # Инициализируем список для хранения publication_text
            publications = []
            
            # Проходимся по строкам CSV файла
            for row in reader:
                # Проверяем, соответствует ли user_id текущей строке
                if row['user_id'] == user_id:
                    # Получаем дату и время публикации из строки и преобразуем их в объект datetime
                    publication_date = datetime.strptime(row['publication_date'], '%Y-%m-%d %H:%M:%S')
                    
                    # Проверяем, находится ли публикация в пределах последних 24 часов
                    if current_datetime - publication_date <= timedelta(hours=24):
                        # Если да, добавляем текст публикации в список
                        publications.append(row['publication_text'])
            
            return publications
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return []



# TEST
csv_file = '/Users/vladimirkadnikov/elbrus/NewsBuddy/news.csv'
user_id = '6555020781'
publications_24 = get_news(csv_file, user_id)
# print(publications_24)
# for publication in publications_24:
#     print(publication)


# ГЕНЕРИМ ОБЛАКО С ПОМОЩЬЮ WordCloud 

import matplotlib.pyplot as plt
from wordcloud import WordCloud
import nltk
from nltk.corpus import stopwords
import re
from pymystem3 import Mystem

nltk.download('stopwords')

def clean_text(text):
    mystem = Mystem()
    
    # Загрузите список стоп-слов из NLTK
    stop_words = set(stopwords.words('russian')) 
    
    # Преобразование текста в нижний регистр
    text = text.lower()

    # Удаление ссылок
    text = re.sub(r'http\S+', '', text)
    
    # Удаление символов, не являющихся буквами
    text = re.sub(r'[^а-яА-Яa-zA-Z]', ' ', text)
    
    # Удаление стоп-слов
    words = text.split()
    words = [word for word in words if word not in stop_words]
    
    # Лемматизация слов с использованием Mystem
    lemmatized_words = mystem.analyze(" ".join(words))
    
    # Отбор только существительных
    nouns = [word['analysis'][0]['lex'] for word in lemmatized_words if 'analysis' in word and word['analysis'] and 'S' in word['analysis'][0]['gr']]
    
    # Ограничение на минимальную длину слова в 4 символа
    nouns = [noun for noun in nouns if len(noun) >= 3]
    
    return ' '.join(nouns)


def generate_cloud(publications):
    # Объединяем все тексты публикаций в одну строку
    text = " ".join(publications)
    
    # Очищаем текст
    cleaned_text = clean_text(text)
    print(cleaned_text)
    # Создаем объект WordCloud
    wordcloud = WordCloud(width=800, height=400, background_color='white', max_words = 50).generate(cleaned_text)
    
    # Отображаем облако слов
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.show()

# # Пример использования функции
# if __name__ == "__main__":
#     generate_cloud(publications_24)
