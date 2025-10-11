"""
Telegram Bot для анализа фото по Мета-Методу
Принимает фото + текстовый запрос, анализирует через GPT-4o/4o-mini, возвращает PDF
"""

import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)
from openai import OpenAI
from pdf_generator import create_analysis_pdf
from config import TELEGRAM_TOKEN, OPENAI_API_KEY, OPENAI_MODEL

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация OpenAI клиента
client = OpenAI(api_key=OPENAI_API_KEY)

# Состояния для ConversationHandler
WAITING_FOR_PHOTO, WAITING_FOR_REQUEST = range(2)

# Системный промпт для анализа
SYSTEM_PROMPT = """Ты — Мастер и эксперт Мета-Метода, работающий с энергетикой и подсознанием.
Твоя задача — провести глубокую диагностику на основе фотографии человека и его запроса.

ОБЯЗАТЕЛЬНО учитывай:
1. Визуальные данные с фотографии (энергетика, состояние человека)
2. Текстовый запрос клиента
3. Методологию из Мета-Метода

Структура анализа (строго следуй этой структуре):

**Сканер подсознания по Мета-Методу для [Имя]**

**Запрос:**
[Повтори запрос клиента]

**1) Контракты и подключки**
[Какие неосознанные контракты и энергетические подключки видны]

**2) Слои**
[Из какого периода жизни идёт программа]

**3) Поток энергии по центрам**
[Как распределяется энергия по чакрам/центрам]

**4) Главные программы**
[Какие основные убеждения и программы блокируют]

**5) Главные уроки души**
[Что душа пришла проработать в этом воплощении]

**6) Родовые влияния**
[Какие родовые программы влияют]

**7) Связи из прошлых жизней**
[Если есть влияние кармических программ]

**8) Что важно изменить**
[Конкретные шаги для трансформации]

**9) Трансформационные фразы**
[Мощные аффирмации для перепрошивки. Начинай с: "Я признаю и даю место всем опытам..."]

**10) Рекомендация: следующий шаг**
[Практический совет на ближайшее время]

Пиши глубоко, точно, с сердцем. Используй метафоры и образы. Будь конкретной, но бережной.
"""


class UserSession:
    """Хранит данные сессии пользователя"""
    def __init__(self):
        self.photo_path = None
        self.request_text = None
        self.username = None


# Словарь для хранения сессий пользователей
user_sessions = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало работы с ботом"""
    user_id = update.effective_user.id
    username = update.effective_user.first_name or "Друг"

    user_sessions[user_id] = UserSession()
    user_sessions[user_id].username = username

    welcome_message = f"""Привет, {username}! 👋

Я — бот для проведения диагностики по Мета-Методу.

**Как я работаю:**
1. Ты отправляешь мне своё фото
2. Пишешь свой запрос (что хочешь проработать)
3. Я провожу глубокий анализ через GPT-4o с учетом твоего фото и запроса
4. Ты получаешь детальный разбор в формате красивого PDF файла

**Начнём?**
Отправь мне своё фото (лицо должно быть хорошо видно).
"""

    await update.message.reply_text(welcome_message)
    return WAITING_FOR_PHOTO


async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение фото от пользователя"""
    user_id = update.effective_user.id

    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession()

    # Получаем фото лучшего качества
    photo_file = await update.message.photo[-1].get_file()

    # Создаём папку для фото, если её нет
    os.makedirs('user_photos', exist_ok=True)

    # Сохраняем фото
    photo_path = f'user_photos/{user_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg'
    await photo_file.download_to_drive(photo_path)

    user_sessions[user_id].photo_path = photo_path

    await update.message.reply_text(
        "Отлично! Фото получено. ✨\n\n"
        "Теперь напиши свой запрос. Например:\n"
        "• Не хватает финансов, хочу выйти на новый уровень дохода\n"
        "• Хочу встретить свою судьбу и построить счастливые отношения\n"
        "• Хочу реализоваться и перестать бояться проявляться публично\n"
        "• Что блокирует мой бизнес/здоровье/творчество?"
    )

    return WAITING_FOR_REQUEST


async def receive_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение текстового запроса и запуск анализа"""
    user_id = update.effective_user.id

    if user_id not in user_sessions or not user_sessions[user_id].photo_path:
        await update.message.reply_text(
            "Сначала отправь фото! Используй /start для начала."
        )
        return ConversationHandler.END

    user_sessions[user_id].request_text = update.message.text

    # Показываем что работаем
    processing_msg = await update.message.reply_text(
        "⏳ Провожу глубокий анализ...\n"
        "Это может занять 30-60 секунд.\n"
        "Я учитываю твоё фото и запрос. 🔮"
    )

    try:
        # Выполняем анализ через GPT-4o
        analysis_result = await analyze_with_gpt4o(
            user_sessions[user_id].photo_path,
            user_sessions[user_id].request_text,
            user_sessions[user_id].username
        )

        # Генерируем PDF
        pdf_path = create_analysis_pdf(
            analysis_result,
            user_sessions[user_id].username,
            user_sessions[user_id].request_text
        )

        # Отправляем PDF
        with open(pdf_path, 'rb') as pdf_file:
            await update.message.reply_document(
                document=pdf_file,
                filename=f"Сканер_подсознания_{user_sessions[user_id].username}.pdf",
                caption="✨ Твой персональный Сканер подсознания готов!\n\n"
                        "Работай с трансформационными фразами каждый день. 🙏"
            )

        # Удаляем сообщение о процессе
        await processing_msg.delete()

        # Очищаем фото (опционально)
        # os.remove(user_sessions[user_id].photo_path)
        # os.remove(pdf_path)

        # Предлагаем новый анализ
        keyboard = [[InlineKeyboardButton("Провести новый анализ", callback_data="new_analysis")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Хочешь провести ещё один анализ?",
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        await processing_msg.edit_text(
            f"❌ Произошла ошибка при анализе.\n"
            f"Попробуй ещё раз через /start\n\n"
            f"Ошибка: {str(e)}"
        )

    return ConversationHandler.END


async def analyze_with_gpt4o(photo_path: str, request_text: str, username: str) -> str:
    """
    Анализ через GPT-4o Vision
    ВАЖНО: учитывает и фото, и текстовый запрос
    """
    import base64

    # Читаем фото и конвертируем в base64
    with open(photo_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    # Формируем запрос к GPT-4o с Vision
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Проведи анализ для человека по имени {username}.\n\nЗапрос клиента: {request_text}\n\nУчитывай энергетику и состояние с фотографии."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high"  # Высокое качество анализа
                        }
                    }
                ]
            }
        ],
        max_tokens=4000,
        temperature=0.8,  # Чуть больше креативности для глубины анализа
    )

    return response.choices[0].message.content


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()

    if query.data == "new_analysis":
        user_id = query.from_user.id
        username = query.from_user.first_name or "Друг"

        user_sessions[user_id] = UserSession()
        user_sessions[user_id].username = username

        await query.message.reply_text(
            "Отлично! Начнём новый анализ. 🌟\n\n"
            "Отправь мне фото."
        )
        return WAITING_FOR_PHOTO

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена текущей операции"""
    await update.message.reply_text(
        "Операция отменена. Используй /start чтобы начать заново."
    )
    return ConversationHandler.END


def main():
    """Запуск бота"""
    # Создаём приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # ConversationHandler для управления диалогом
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WAITING_FOR_PHOTO: [
                MessageHandler(filters.PHOTO, receive_photo),
            ],
            WAITING_FOR_REQUEST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_request),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Добавляем обработчики
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_callback))

    # Запускаем бота
    logger.info("Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
