"""
Конфигурация бота
Заполни свои токены и ключи
"""

import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла (если есть)
load_dotenv()

# Telegram Bot Token - получи у @BotFather
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN_HERE')

# OpenAI API Key - получи на platform.openai.com
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'YOUR_OPENAI_API_KEY_HERE')

# Модель OpenAI для использования
# Рекомендуется: 'gpt-4o' для максимального качества или 'gpt-4o-mini' для экономии
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')

# Максимальное количество токенов для ответа
MAX_TOKENS = int(os.getenv('MAX_TOKENS', '4000'))

# Температура генерации (0.0 - 1.0)
# Выше = более креативно, ниже = более предсказуемо
TEMPERATURE = float(os.getenv('TEMPERATURE', '0.8'))

# PostgreSQL Database настройки
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
POSTGRES_DB = os.getenv('POSTGRES_DB', 'metamethod_bot')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
