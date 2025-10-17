"""
Вспомогательные функции для работы с именами пользователей
"""

import re
from openai import OpenAI
from config import OPENAI_API_KEY


def extract_name_from_request(request_text: str) -> str:
    """
    Пытается извлечь имя из текста запроса
    Ищет паттерны типа "Меня зовут...", "Я - ...", имя в начале и т.д.
    """
    # Паттерны для поиска имени
    patterns = [
        r'[Мм]еня зовут\s+([А-ЯЁ][а-яё]+)',
        r'[Яя]\s+[-—]\s+([А-ЯЁ][а-яё]+)',
        r'[Яя]\s+([А-ЯЁ][а-яё]+)\s+и',  # "Я Мария и хочу..."
        r'[Яя]\s+([А-ЯЁ][а-яё]+)[\.,]',
        r'^([А-ЯЁ][а-яё]+)[\.,]',  # Имя в начале с запятой/точкой
    ]

    for pattern in patterns:
        match = re.search(pattern, request_text)
        if match:
            return match.group(1)

    return None


def get_name_declensions_gpt(name: str) -> dict:
    """
    Получает склонения имени через GPT для правильной грамматики
    Возвращает словарь с падежами
    """
    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""Просклоняй русское имя "{name}" по падежам.
Верни ТОЛЬКО JSON в таком формате (без комментариев, без markdown):
{{
  "nominative": "Наталья",
  "genitive": "Натальи",
  "dative": "Наталье",
  "accusative": "Наталью",
  "instrumental": "Натальей",
  "prepositional": "Наталье"
}}

Если имя мужское, склоняй соответственно (Даниил → Даниила, Даниилу и т.д.)"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150
        )

        result_text = response.choices[0].message.content.strip()

        # Убираем markdown если есть
        result_text = result_text.replace('```json', '').replace('```', '').strip()

        import json
        declensions = json.loads(result_text)

        return declensions

    except Exception as e:
        # Fallback - возвращаем имя как есть во всех падежах
        print(f"Ошибка склонения имени: {e}")
        return {
            "nominative": name,
            "genitive": name,
            "dative": name,
            "accusative": name,
            "instrumental": name,
            "prepositional": name
        }


def replace_pronouns_with_name(text: str, declensions: dict) -> str:
    """
    Заменяет личные местоимения (ты, тебе, тебя) на имя в правильном падеже.
    НЕ заменяет притяжательные местоимения (твой, твоя и т.д.) - это звучит неестественно.
    """
    if not declensions:
        return text

    # Маппинг ТОЛЬКО личных местоимений на падежи
    # Притяжательные (твой, твоя и т.д.) НЕ заменяем
    replacements = [
        # Родительный падеж (кого? - у тебя, для тебя, без тебя)
        (r'\b([Уу]|[Дд]ля|[Бб]ез|[Оо]т|[Ии]з-за|[Кк]роме)\s+тебя\b', lambda m: f'{m.group(1)} {declensions["genitive"]}'),

        # Дательный падеж (кому? - тебе, Тебе)
        (r'\b[Тт]ебе\b', f'{declensions["dative"]}'),

        # Винительный падеж (кого? - тебя, на тебя, про тебя)
        (r'\b([Нн]а|[Пп]ро|[Зз]а|[Вв])\s+тебя\b', lambda m: f'{m.group(1)} {declensions["accusative"]}'),

        # Творительный падеж (кем? - с тобой, за тобой, перед тобой)
        (r'\b([Сс]|[Сс]о|[Зз]а|[Пп]еред|[Нн]ад|[Пп]од)\s+тобой\b', lambda m: f'{m.group(1)} {declensions["instrumental"]}'),
        (r'\b[Тт]обою\b', f'{declensions["instrumental"]}'),

        # Именительный падеж (кто? - ты, Ты)
        (r'\b[Тт]ы\b', f'{declensions["nominative"]}'),
    ]

    result = text
    for pattern, replacement in replacements:
        if callable(replacement):
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        else:
            result = re.sub(pattern, replacement, result)

    return result
