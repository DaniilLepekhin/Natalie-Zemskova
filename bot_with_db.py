"""
Telegram Bot для анализа фото по Мета-Методу + PostgreSQL
Все анализы сохраняются в БД для подготовки датасета
"""

import os
import logging
import time
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
from database import get_db
from metamethod_analyzer import analyze_with_metamethod

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация OpenAI клиента
client = OpenAI(api_key=OPENAI_API_KEY)

# Инициализация БД
db = get_db()

# Состояния для ConversationHandler
WAITING_FOR_PHOTO, WAITING_FOR_REQUEST = range(2)

# Системный промпт для анализа - читаем из файла
with open('prompt_final.txt', 'r', encoding='utf-8') as f:
    SYSTEM_PROMPT = f.read()


class UserSession:
    """Хранит данные сессии пользователя"""
    def __init__(self):
        self.photo_path = None
        self.request_text = None
        self.username = None
        self.start_time = None


# Словарь для хранения сессий пользователей
user_sessions = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало работы с ботом"""
    user_id = update.effective_user.id
    username = update.effective_user.first_name or "Друг"
    telegram_username = update.effective_user.username
    last_name = update.effective_user.last_name

    # Сохраняем/обновляем пользователя в БД
    db.create_or_update_user(
        user_id=user_id,
        username=telegram_username,
        first_name=username,
        last_name=last_name
    )

    user_sessions[user_id] = UserSession()
    user_sessions[user_id].username = username
    user_sessions[user_id].start_time = time.time()

    welcome_message = f"""Привет, {username}! 👋

Я — бот для практики самопознания по Мета-Методу.

<b>Как я работаю:</b>
1. Ты отправляешь мне своё фото
2. Пишешь свой запрос — что хочешь проработать в себе
3. Я создаю для тебя глубокий разбор через GPT-4o
4. Ты получаешь красивый PDF с практиками трансформации

<b>Примеры запросов:</b>
• Хочу выйти на новый уровень дохода
• Не получается построить гармоничные отношения
• Постоянная усталость и выгорание
• Страх проявляться и реализовываться

<b>Начнём?</b>
Отправь мне своё фото (можно с подписью-запросом).
"""

    await update.message.reply_text(welcome_message, parse_mode='HTML')
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

    # Проверяем, есть ли подпись к фото (caption)
    caption = update.message.caption
    if caption and len(caption.strip()) > 10:  # Если есть осмысленная подпись
        # Сохраняем запрос из подписи
        user_sessions[user_id].request_text = caption.strip()

        # Показываем что работаем
        processing_msg = await update.message.reply_text(
            "⏳ Провожу глубокий многоуровневый анализ...\n"
            "Это займёт 30-60 секунд.\n"
            "Я прохожу через 5 этапов: программы → род → чакры → фразы → компоновка 🔮✨"
        )

        # Сразу запускаем анализ
        return await process_analysis(update, context, processing_msg)
    else:
        # Если подписи нет - просим написать запрос
        await update.message.reply_text(
            "Отлично! Фото получено. ✨\n\n"
            "Теперь напиши свой запрос. Например:\n"
            "• Не хватает финансов, хочу выйти на новый уровень дохода\n"
            "• Хочу встретить свою судьбу и построить счастливые отношения\n"
            "• Хочу реализоваться и перестать бояться проявляться публично\n"
            "• Что блокирует мой бизнес/здоровье/творчество?"
        )
        return WAITING_FOR_REQUEST


async def process_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE, processing_msg) -> int:
    """Выполнение анализа и отправка результата"""
    user_id = update.effective_user.id

    try:
        start_time = time.time()

        # Выполняем анализ через multi-step MetaMethod analyzer
        analysis_result, tokens_used = await analyze_with_metamethod(
            user_sessions[user_id].request_text,
            user_sessions[user_id].username
        )

        processing_time = int(time.time() - start_time)

        # Генерируем PDF
        pdf_path = create_analysis_pdf(
            analysis_result,
            user_sessions[user_id].username,
            user_sessions[user_id].request_text
        )

        # Сохраняем в БД
        analysis_id = db.save_analysis(
            user_id=user_id,
            photo_path=user_sessions[user_id].photo_path,
            request_text=user_sessions[user_id].request_text,
            analysis_result=analysis_result,
            pdf_path=pdf_path,
            processing_time=processing_time,
            tokens_used=tokens_used,
            model_used=OPENAI_MODEL
        )

        # Сохраняем фото в base64 для датасета
        db.save_photo_base64(analysis_id, user_sessions[user_id].photo_path)

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

        # Предлагаем новый анализ
        keyboard = [[InlineKeyboardButton("Провести новый анализ", callback_data="new_analysis")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Хочешь провести ещё один анализ?",
            reply_markup=reply_markup
        )

        logger.info(f"✅ Анализ #{analysis_id} завершён для пользователя {user_id} за {processing_time}с")

    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        await processing_msg.edit_text(
            f"❌ Произошла ошибка при анализе.\n"
            f"Попробуй ещё раз через /start\n\n"
            f"Ошибка: {str(e)}"
        )

    return ConversationHandler.END


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
        "⏳ Провожу глубокий многоуровневый анализ...\n"
        "Это займёт 30-60 секунд.\n"
        "Я прохожу через 5 этапов: программы → род → чакры → фразы → компоновка 🔮✨"
    )

    return await process_analysis(update, context, processing_msg)


async def analyze_with_gpt4o(photo_path: str, request_text: str, username: str) -> tuple:
    """
    Анализ через GPT-4o Vision
    Возвращает (результат, использованные токены)
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
                        "text": f"Человек по имени {username} делится своим образом для практики самопознания и духовного роста.\n\nЗапрос: {request_text}\n\nПосмотри на образ - что передаёт выражение, какая энергетика считывается, что чувствуется. Используй это как дополнительный контекст для глубины практики."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        max_tokens=4000,
        temperature=0.8,
    )

    result_text = response.choices[0].message.content
    tokens_used = response.usage.total_tokens

    return result_text, tokens_used


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()

    if query.data == "new_analysis":
        user_id = query.from_user.id
        username = query.from_user.first_name or "Друг"
        telegram_username = query.from_user.username
        last_name = query.from_user.last_name

        # Обновляем пользователя в БД
        db.create_or_update_user(
            user_id=user_id,
            username=telegram_username,
            first_name=username,
            last_name=last_name
        )

        user_sessions[user_id] = UserSession()
        user_sessions[user_id].username = username
        user_sessions[user_id].start_time = time.time()

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


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для просмотра статистики (для админа)"""
    user_id = update.effective_user.id

    try:
        # Получаем статистику пользователя
        user_stats = db.get_user_stats(user_id)
        recent = db.get_recent_analyses(limit=5)
        themes = db.get_theme_statistics()

        stats_text = f"""📊 <b>Твоя статистика</b>

Всего анализов: {user_stats['total_analyses']}
Зарегистрирован: {user_stats['created_at'].strftime('%d.%m.%Y')}
Последняя активность: {user_stats['last_active'].strftime('%d.%m.%Y %H:%M')}

<b>Популярные темы:</b>
"""
        for theme in themes[:5]:
            stats_text += f"• {theme['theme']}: {theme['count']}\n"

        await update.message.reply_text(stats_text, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Error in stats: {e}")
        await update.message.reply_text("Ошибка получения статистики")


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
    application.add_handler(CommandHandler('stats', stats_command))

    # Запускаем бота
    logger.info("🤖 Бот запущен с интеграцией PostgreSQL!")
    logger.info(f"📊 Модель: {OPENAI_MODEL}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
