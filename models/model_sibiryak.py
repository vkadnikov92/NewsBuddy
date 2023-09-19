import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# https://huggingface.co/SiberiaSoft/SiberianFredT5-instructor
model_name = "SiberiaSoft/SiberianFredT5-instructor"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

model.to("cpu")

# def generate(prompt):
#   data = tokenizer('<SC6>' + prompt + '\nОтвет: <extra_id_0>', return_tensors="pt")
#   data = {k: v.to(model.device) for k, v in data.items()}
#   output_ids = model.generate(
#       **data,  do_sample=True, temperature=0.2, max_new_tokens=512, top_p=0.95, top_k=5, repetition_penalty=1.03, no_repeat_ngram_size=2
#   )[0]
#   out = tokenizer.decode(output_ids.tolist())
#   out = out.replace("<s>","").replace("</s>","")
#   return out

# Функция для генерации текста
def generate(text):
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
        no_repeat_ngram_size=2
    )[0]
    
    # Декодирование и возврат результата
    out = tokenizer.decode(output_ids.tolist())
    out = out.replace("<s>", "").replace("</s>", "")
    return out


# Пример использования
text = '''
Поединок, который мог бы затмить бой Маска и Цукерберга, — Алёна Водонаева написала ещё одно заявление на Андрея Петрова. Она хочет, чтобы его посадили за дискредитацию российской армии.
Водонаева и Петров поссорились ещё весной. Тогда Алёна опубликовала шуточный пост в запрещённой в России инсте, где она вместе с собакой Рексом «готовится вступить в ЧВК "Вагнер"».
По данным «Базы», полиция приняла заявления от Водонаевой, и теперь сотрудники внимательно изучают канал Петрова.
'''

summary = generate(text)

print(text)
print('')
print('==================================')
print('')
print(f"Саммари: {summary}")


