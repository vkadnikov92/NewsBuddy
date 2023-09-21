import re
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# https://huggingface.co/SiberiaSoft/SiberianFredT5-instructor
model_name = "SiberiaSoft/SiberianFredT5-instructor"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

model.to("cpu")

# def generate_summary(text):
#   prompt = 'Выдели главные мысли в новости:'
#   data = tokenizer('<SC6>' + prompt + text + '\nОтвет: <extra_id_0>', return_tensors="pt")
#   data = {k: v.to(model.device) for k, v in data.items()}
#   output_ids = model.generate(
#       **data,  do_sample=True, temperature=0.2, max_new_tokens=512, top_p=0.95, top_k=5, repetition_penalty=1.03, no_repeat_ngram_size=2
#   )[0]
#   out = tokenizer.decode(output_ids.tolist())
#   out = out.replace("<s>","").replace("</s>","").replace("<pad>", "").replace("<extra_id_0>", "").strip()
#   return out

# Функция для генерации текста
def generate_summary(text):
    # Очистка текста от слов, начинающихся с @
    text = re.sub(r'@\w+', '', text)
    
    # Подготовка входных данных
    prompt = 'Выдели главные мысли в новости:'
    data = tokenizer('<SC6>' + prompt + text + '\nОтвет: <extra_id_0>', return_tensors="pt")
    data = {k: v.to(model.device) for k, v in data.items()}
    
    # Генерация текста
    output_ids = model.generate(
        **data,
        do_sample=True,
        temperature=0.2,
        max_new_tokens=512,
        top_p=0.95,
        top_k=5,
        repetition_penalty=1.03,
        no_repeat_ngram_size=4
    )[0]
    
    # Декодирование и возврат результата
    out = tokenizer.decode(output_ids.tolist())
    out = out.replace("<s>", "").replace("</s>", "").replace("<pad>", "").replace("<extra_id_0>", "").strip()
    return out


# # Пример использования
# text = '''
# Поединок, который мог бы затмить бой Маска и Цукерберга, — Алёна Водонаева написала ещё одно заявление на Андрея Петрова. Она хочет, чтобы его посадили за дискредитацию российской армии.
# Водонаева и Петров поссорились ещё весной. Тогда Алёна опубликовала шуточный пост в запрещённой в России инсте, где она вместе с собакой Рексом «готовится вступить в ЧВК "Вагнер"».
# По данным «Базы», полиция приняла заявления от Водонаевой, и теперь сотрудники внимательно изучают канал Петрова.
# '''

# text2 = '''
# Бывший нападающий «Нефтехимика» Самуэль Бучек, ныне выступающий за чешский клуб «Оцеларжи Тршинец», рассказал, как ему не дали пробиться в состав «Сиэтл Кракен», почему он выбрал продолжение карьеры в КХЛ и как покинул Россию.

# «Всё началось, когда я прибыл в лагерь, когда агент сказал мне по телефону, что я должен получить двусторонний контракт, на что я согласился. Я прилетел в Сиэтл, пообщался с менеджерами, скаутом, который следил за мной весь сезон, главным тренером и тренером фарм-клуба. Мне сказали, что знают, что я снайпер, но 54 гола в словацкой Экстралиге ничего не значат. В конце концов сообщили, что дадут мне контракт только на АХЛ и ECHL, что меня шокировало, ведь по телефону мне рассказали о контракте НХЛ и АХЛ.

# Я сказал себе, что не буду сворачивать дело, буду бороться. Потом ко мне подсел тренер фарм-клуба, который прямо сказал мне, что, поскольку у меня худший контракт, он может рассчитывать на меня только как на игрока третьего-четвёртого звена. Будут играть хоккеисты, у которых двусторонний контракт. В конце концов, я снайпер, а не игрок низших звеньев, поэтому решил не подписывать контракт и поехать в Европу.
# '''


# summary = generate_summary(text2)

# print(text2)
# print('')
# print('==================================')
# print('')
# print(f"Саммари: {summary}")


