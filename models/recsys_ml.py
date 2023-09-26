import joblib
# joblib.load('models/classifier.pkl')
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords
import random
import pandas as pd

nltk.download('stopwords')
russian_stop_words = stopwords.words("russian")
tfidf_vectorizer = TfidfVectorizer(max_features=5000, stop_words=russian_stop_words)
classifier = joblib.load('models/classifier.pkl')
tfidf_vectorizer = joblib.load('models/tfidf_vectorizer.pkl')

def get_categories(user_id, news):
    predicted_channel_category = []
    user_id_to_select = user_id
    user_data = news[news['user_id'] == user_id_to_select]  # news заменяем на наш файл с новостями
    user_data_grouped = user_data.groupby('channel_name')
    for channel_name, channel_data in user_data_grouped:
        channel_news_texts = channel_data['publication_text'].tolist()
        channel_news_tfidf = tfidf_vectorizer.transform(channel_news_texts)
        channel_news_predictions = classifier.predict(channel_news_tfidf)
        predicted_channel_category.append(
            max(set(channel_news_predictions), key=channel_news_predictions.tolist().count))
    return predicted_channel_category


def suggestions(predicted_channel_category, category_to_channels):
    unique_categories = set(predicted_channel_category)

    recommended_channels = []

    if len(unique_categories) == 1:
        category = unique_categories.pop()
        channels_in_category = category_to_channels.get(category, [])
        random.shuffle(channels_in_category)  
        recommended_channels = channels_in_category[:4]
    elif len(unique_categories) == 2:
        for category in unique_categories:
            channels_in_category = category_to_channels.get(category, [])
            random.shuffle(channels_in_category)
            recommended_channels.extend(channels_in_category[:2])
    elif len(unique_categories) == 3:
        for category in unique_categories:
            channels_in_category = category_to_channels.get(category, [])
            random.shuffle(channels_in_category)
            recommended_channels.extend(channels_in_category[:2])

    return recommended_channels


category_to_channels = {
    'новости': [
        'https://t.me/breakingmash',
        'https://t.me/lentachold',
        'https://t.me/astrapress',
        'https://t.me/lentachold',
        'https://t.me/theinsider',
        'https://t.me/otsuka_bld',
        'https://t.me/meduzalive',
        'https://t.me/guardian',
    ],
    'юмор': [
        'https://t.me/ia_panorama',
        'https://t.me/dvachannel',
        'https://t.me/pezduzalive',
        'https://t.me/mudak',
        'https://t.me/cats_cats',
        'https://t.me/Reddit',
        'https://t.me/paperpublic',
        'https://t.me/thedankestmemes',
        'https://t.me/memes',
        'https://t.me/community_memy',
    ],
    'технологии': [
        'https://t.me/bugnotfeature',
        'https://t.me/prostinas',
        'https://t.me/it_teech',
        'https://t.me/rozetked',
        'https://t.me/yandex',
        'https://t.me/junior_developer_ua',
        'https://t.me/htech_plus',
        'https://t.me/cyberfreek',
        'https://t.me/python2day',
        'https://t.me/addmeto',
    ],
    'экономика': [
        'https://t.me/zeroton',
        'https://t.me/guriev_sm',
        'https://t.me/financelist',
        'https://t.me/proeconomics',
        'https://t.me/hoolinomics',
        'https://t.me/dohod',
        'https://t.me/prime1',
        'https://t.me/AK47pfl',
        'https://t.me/forbesrussia',
        'https://t.me/selfinvestor',
    ],
    'игры': [
        'https://t.me/+VIuvvPWhb-mR4BRq',
        'https://t.me/Dota2',
        'https://t.me/egs_tg',
        'https://t.me/vgtimes',
        'https://t.me/stopgamenews',
        'https://t.me/PROgame_news',
        'https://t.me/GamezTop7',
        'https://t.me/gamerbay',
        'https://t.me/combobreaker',
        'https://t.me/progamedev',
    ],
    'спорт': [
        'https://t.me/championat',
        'https://t.me/Match_TV',
        'https://t.me/myachPRO',
        'https://t.me/sportsru',
        'https://t.me/QryaProDucktion',
        'https://t.me/sjbodyfit',
        'https://t.me/fiztransform',
        'https://t.me/sportsmens1',
        'https://t.me/runforhealth',
        'https://t.me/sportazarto',
    ],
}


def generate_recommendations(user_id, news_csv_path, category_to_channels):
    try:
        news = pd.read_csv(news_csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return []
    
    try:
        predicted_channel_category = get_categories(user_id, news)
    except Exception as e:
        print(f"Error getting categories: {e}")
        return []

    try:
        recommended_channels = suggestions(predicted_channel_category, category_to_channels)
    except Exception as e:
        print(f"Error getting suggestions: {e}")
        return []
    return recommended_channels


# # Inference
# news = pd.read_csv('NewsBuddy/news.csv')
# rec = suggestions(get_categories(6555020781, news), category_to_channels)
# print(rec)

# rec2 = generate_recommendations(6555020781,'/Users/vladimirkadnikov/elbrus/NewsBuddy/news.csv',category_to_channels)
# print(rec2)