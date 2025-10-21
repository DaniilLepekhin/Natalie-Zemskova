"""
Telegram Bot для анализа фото по Мета-Методу с воронкой продаж
Включает: мини-квиз, автодожимы, проверку оплаты
"""

import os
import logging
import time
from datetime import datetime, timedelta
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
from pdf_generator_with_background import generate_pdf
from config import TELEGRAM_TOKEN, OPENAI_API_KEY, OPENAI_MODEL
from database import get_db
from metamethod_analyzer import analyze_with_metamethod
from sales_funnel_texts import *
from name_helper import extract_name_from_request, get_name_declensions_gpt, replace_pronouns_with_name
import asyncio

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
(QUIZ_STATE, WAITING_FOR_PHOTO, WAITING_FOR_REQUEST, WAITING_FOR_NAME,
 WAITING_PAYMENT, PAID_USER, CHECKING_FREE_ACCESS) = range(7)


class UserSession:
    """Хранит данные сессии пользователя"""
    def __init__(self):
        self.photo_path = None
        self.request_text = None
        self.username = None
        self.start_time = None
        self.quiz_answer = None
        self.payment_status = None  # None, 'pending', 'paid'
        self.funnel_stage = 'start'  # start, quiz, about, examples, pricing, paid
        self.last_funnel_message_time = None
        self.scans_count = 0  # Количество доступных сканирований
        self.subscription_type = None  # '1scan', '3scans', 'year', 'vip'


# Словарь для хранения сессий пользователей
user_sessions = {}


# ===== ВОРОНКА ПРОДАЖ =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало работы с ботом - показываем мини-квиз или проверку доступа"""
    user_id = update.effective_user.id
    username = update.effective_user.first_name or "Друг"
    telegram_username = update.effective_user.username
    last_name = update.effective_user.last_name

    # Проверяем deep link параметр
    start_param = context.args[0] if context.args else None

    # Если это проверка бесплатного доступа
    if start_param == 'checkdostup':
        await update.message.reply_text(CHECK_ACCESS_START, parse_mode='HTML')

        # Инициализируем сессию
        user_sessions[user_id] = UserSession()
        user_sessions[user_id].username = username
        user_sessions[user_id].funnel_stage = 'check_access'

        return CHECKING_FREE_ACCESS

    # Если это бесплатное сканирование без оплаты
    if start_param == 'freescan':
        # Сохраняем пользователя в БД
        db.create_or_update_user(
            user_id=user_id,
            username=telegram_username,
            first_name=username,
            last_name=last_name
        )

        # Инициализируем сессию с неограниченным доступом
        user_sessions[user_id] = UserSession()
        user_sessions[user_id].username = username
        user_sessions[user_id].payment_status = 'free'
        user_sessions[user_id].scans_count = 999  # Безлимит
        user_sessions[user_id].funnel_stage = 'free_access'

        await update.message.reply_text(
            "🌿 Добро пожаловать!\n\n"
            "Ты можешь пройти сканирование прямо сейчас.\n\n"
            "Отправь мне своё фото (селфи в полный рост или портрет), "
            "и я проведу диагностику твоего энергетического состояния 💫",
            parse_mode='HTML'
        )

        return WAITING_FOR_PHOTO

    # Сохраняем/обновляем пользователя в БД
    db.create_or_update_user(
        user_id=user_id,
        username=telegram_username,
        first_name=username,
        last_name=last_name
    )

    # Инициализируем сессию
    user_sessions[user_id] = UserSession()
    user_sessions[user_id].username = username
    user_sessions[user_id].start_time = time.time()
    user_sessions[user_id].last_funnel_message_time = datetime.now()
    user_sessions[user_id].funnel_stage = 'welcome'

    # Показываем приветствие (без квиза)
    keyboard = [
        [InlineKeyboardButton("Да, хочу пройти сканирование", callback_data='goto_pricing')],
        [InlineKeyboardButton("Хочу узнать подробнее", callback_data='about_scanner')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(WELCOME_MESSAGE, reply_markup=reply_markup, parse_mode='HTML')

    # Запускаем фоновую задачу для отложенных дожимов
    asyncio.create_task(schedule_followups(user_id, context))

    return QUIZ_STATE


async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ответа на квиз"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    quiz_choice = query.data.replace('quiz_', '')

    if user_id in user_sessions:
        user_sessions[user_id].quiz_answer = quiz_choice
        user_sessions[user_id].funnel_stage = 'quiz_result'

    # Показываем адаптированный пример
    await query.message.reply_text(
        QUIZ_EXAMPLES[quiz_choice],
        parse_mode='HTML'
    )

    # TODO: Здесь отправить пример PDF для выбранной сферы
    # await query.message.reply_document(...)

    # Кнопка перехода к приветствию
    keyboard = [[InlineKeyboardButton("✨ Узнать про Сканер подробнее", callback_data='show_welcome')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        "Хочешь такой же результат? 👇",
        reply_markup=reply_markup
    )

    return QUIZ_STATE


async def show_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показать приветственное сообщение"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id in user_sessions:
        user_sessions[user_id].funnel_stage = 'welcome'

    keyboard = [
        [InlineKeyboardButton("Да, хочу пройти сканирование", callback_data='goto_pricing')],
        [InlineKeyboardButton("Хочу узнать подробнее", callback_data='about_scanner')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(WELCOME_MESSAGE, reply_markup=reply_markup, parse_mode='HTML')
    return QUIZ_STATE


async def about_scanner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Информация о сканере"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id in user_sessions:
        user_sessions[user_id].funnel_stage = 'about'

    # TODO: Отправить фото по 7 чакрам
    # await query.message.reply_photo(photo=open('chakras_photo.jpg', 'rb'))

    keyboard = [
        [InlineKeyboardButton("📂 Посмотреть примеры сканирования", callback_data='show_examples')],
        [InlineKeyboardButton("⚡ Пройти сканирование", callback_data='goto_pricing')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(ABOUT_SCANNER, reply_markup=reply_markup, parse_mode='HTML')
    return QUIZ_STATE


async def show_examples(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показать примеры сканирований"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id in user_sessions:
        user_sessions[user_id].funnel_stage = 'examples'

    # TODO: Отправить скрины примеров
    # await query.message.reply_photo(photo=open('example1.jpg', 'rb'))
    # await query.message.reply_photo(photo=open('example2.jpg', 'rb'))
    # await query.message.reply_photo(photo=open('example3.jpg', 'rb'))

    keyboard = [[InlineKeyboardButton("✨ Хочу своё сканирование", callback_data='goto_pricing')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Объединяем текст примеров и призыв к действию в одно сообщение
    full_message = f"{EXAMPLES_MESSAGE}\n\nГотова получить своё? 👇"
    await query.message.reply_text(full_message, reply_markup=reply_markup, parse_mode='HTML')
    return QUIZ_STATE


async def show_pricing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показать тарифы"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id in user_sessions:
        user_sessions[user_id].funnel_stage = 'pricing'

    # TODO: Отправить продающую презентацию
    # await query.message.reply_photo(photo=open('pricing_presentation.jpg', 'rb'))

    # Формируем ссылки с подстановкой tg_id пользователя
    tarif1_url = f"https://lizaperman.online/scaner_fullpay_tarif1?tg_id={user_id}"
    tarif2_url = f"https://lizaperman.online/scaner_fullpay_tarif2?tg_id={user_id}"
    tarif3_url = f"https://lizaperman.online/scaner_fullpay_tarif3?tg_id={user_id}"
    tarif4_url = f"https://lizaperman.online/scaner_fullpay_tarif4?tg_id={user_id}"

    # Кнопки для каждого тарифа
    keyboard = [
        [InlineKeyboardButton("💎 Тариф 1 - Оплатить", url=tarif1_url)],
        [InlineKeyboardButton("✨ Тариф 2 - Оплатить", url=tarif2_url)],
        [InlineKeyboardButton("🌟 Тариф 3 - Оплатить", url=tarif3_url)],
        [InlineKeyboardButton("🔥 Тариф 4 - Оплатить", url=tarif4_url)],
        [InlineKeyboardButton("🔙 Вернуться к описанию", callback_data='about_scanner')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        PRICING_MESSAGE,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    return WAITING_PAYMENT


async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Проверка оплаты (заглушка - нужна интеграция с платёжной системой)"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # TODO: Реальная проверка оплаты через API платёжной системы
    # payment_verified = check_payment_api(user_id)

    # Временно: спрашиваем админа или даём доступ сразу
    # Для продакшена - интеграция с Tinkoff/Yookassa/Stripe

    await query.message.reply_text(
        "⏳ Проверяю статус оплаты...\n"
        "Это может занять до 1 минуты."
    )

    # Имитация проверки
    await asyncio.sleep(2)

    # ВРЕМЕННО: даём доступ всем (для тестирования)
    # В продакшене заменить на реальную проверку
    payment_verified = True

    if payment_verified:
        user_sessions[user_id].payment_status = 'paid'
        user_sessions[user_id].funnel_stage = 'paid'
        user_sessions[user_id].scans_count = 1  # По умолчанию 1 сканирование
        # TODO: Определить тип подписки и установить scans_count

        await query.message.reply_text(
            AFTER_PAYMENT.format(channel_link=CHANNEL_LINK),
            parse_mode='HTML'
        )

        return WAITING_FOR_PHOTO
    else:
        keyboard = [[InlineKeyboardButton("Попробовать снова", callback_data='check_payment')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text(
            "❌ Оплата не найдена.\n"
            "Пожалуйста, проверь:\n"
            "1. Оплата прошла успешно\n"
            "2. Прошло 1-2 минуты после оплаты\n\n"
            "Если оплатила, попробуй через минуту:",
            reply_markup=reply_markup
        )

        return WAITING_PAYMENT


# ===== АВТОМАТИЧЕСКИЕ ДОЖИМЫ =====

async def schedule_followups(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Планирование автоматических дожимов"""

    # Дожим через 24 часа
    await asyncio.sleep(24 * 60 * 60)

    if user_id in user_sessions:
        session = user_sessions[user_id]

        # Отправляем только если не оплатил
        if session.payment_status != 'paid':
            keyboard = [[InlineKeyboardButton("👉 Пройти Сканирование сейчас", callback_data='goto_pricing')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=FOLLOWUP_24H,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Ошибка отправки дожима 24ч для {user_id}: {e}")

    # Дожим через 48 часов
    await asyncio.sleep(24 * 60 * 60)

    if user_id in user_sessions:
        session = user_sessions[user_id]

        if session.payment_status != 'paid':
            keyboard = [[InlineKeyboardButton("👉 Начать Сканирование", callback_data='goto_pricing')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=FOLLOWUP_48H,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Ошибка отправки дожима 48ч для {user_id}: {e}")

    # Дожим через 72 часа
    await asyncio.sleep(24 * 60 * 60)

    if user_id in user_sessions:
        session = user_sessions[user_id]

        if session.payment_status != 'paid':
            keyboard = [[InlineKeyboardButton("👉 Перейти к Сканеру Подсознания", callback_data='goto_pricing')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=FOLLOWUP_72H,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Ошибка отправки дожима 72ч для {user_id}: {e}")


# ===== РАБОТА СО СКАНЕРОМ (для оплативших) =====

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение фото от пользователя"""
    user_id = update.effective_user.id

    # Проверка оплаты (разрешаем 'paid' и 'free')
    if user_id not in user_sessions or user_sessions[user_id].payment_status not in ['paid', 'free']:
        keyboard = [[InlineKeyboardButton("💫 Оплатить доступ", callback_data='goto_pricing')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Для использования Сканера необходимо оплатить доступ 🌿",
            reply_markup=reply_markup
        )
        return QUIZ_STATE

    # Проверка лимита сканирований
    if user_sessions[user_id].scans_count <= 0:
        await update.message.reply_text(
            "У тебя закончились доступные сканирования 😔\n"
            "Приобрети новый пакет для продолжения работы."
        )
        keyboard = [[InlineKeyboardButton("💫 Купить ещё", url=PAYMENT_URL)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Перейти к тарифам:", reply_markup=reply_markup)
        return ConversationHandler.END

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
    if caption and len(caption.strip()) > 10:
        user_sessions[user_id].request_text = caption.strip()

        # Пробуем извлечь имя из подписи
        extracted_name = extract_name_from_request(caption.strip())

        if extracted_name:
            # Имя найдено - запускаем анализ
            user_sessions[user_id].username = extracted_name
            logger.info(f"✅ Имя извлечено из подписи к фото: {extracted_name}")

            processing_msg = await update.message.reply_text(
                "⏳ Провожу глубокий многоуровневый анализ...\n"
                "Это займёт 2-3 минуты.\n"
                "Я прохожу через 5 этапов: программы → род → чакры → фразы → компоновка 🔮✨"
            )

            return await process_analysis(update, context, processing_msg)
        else:
            # Имя не найдено - просим ввести
            await update.message.reply_text(
                "Для персонализации анализа, пожалуйста, напиши своё имя.\n\n"
                "Например: Анна, Дмитрий, Мария"
            )
            return WAITING_FOR_NAME
    else:
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
    """Получение текстового запроса и проверка имени"""
    user_id = update.effective_user.id

    if user_id not in user_sessions or not user_sessions[user_id].photo_path:
        await update.message.reply_text(
            "Сначала отправь фото! Используй /start для начала."
        )
        return ConversationHandler.END

    user_sessions[user_id].request_text = update.message.text

    # Пробуем извлечь имя из запроса
    extracted_name = extract_name_from_request(update.message.text)

    if extracted_name:
        # Имя найдено в запросе
        user_sessions[user_id].username = extracted_name
        logger.info(f"✅ Имя извлечено из запроса: {extracted_name}")
        return await start_analysis(update, context, user_id)
    else:
        # Имя не найдено - просим ввести
        await update.message.reply_text(
            "Для персонализации анализа, пожалуйста, напиши своё имя.\n\n"
            "Например: Анна, Дмитрий, Мария"
        )
        return WAITING_FOR_NAME


async def handle_text_without_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка случая, когда пользователь отправил текст вместо фото"""
    user_id = update.effective_user.id

    if user_id in user_sessions:
        user_sessions[user_id].request_text = update.message.text

        # Пробуем извлечь имя из запроса
        extracted_name = extract_name_from_request(update.message.text)

        if extracted_name:
            # Имя найдено в запросе
            user_sessions[user_id].username = extracted_name
            logger.info(f"✅ Имя извлечено из запроса: {extracted_name}")
            await update.message.reply_text(
                "Отлично! Запрос получен. ✨\n\n"
                "Теперь отправь своё фото для анализа."
            )
        else:
            # Имя не найдено - просим ввести
            await update.message.reply_text(
                "Для персонализации анализа, пожалуйста, напиши своё имя.\n\n"
                "Например: Анна, Дмитрий, Мария"
            )
            return WAITING_FOR_NAME
    else:
        await update.message.reply_text(
            "Пожалуйста, начни с команды /start"
        )
        return ConversationHandler.END

    return WAITING_FOR_PHOTO


async def handle_photo_after_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка случая, когда фото пришло после текстового запроса"""
    user_id = update.effective_user.id

    if user_id not in user_sessions or not user_sessions[user_id].request_text:
        await update.message.reply_text(
            "Что-то пошло не так. Давай начнём заново с /start"
        )
        return ConversationHandler.END

    # Получаем фото
    photo_file = await update.message.photo[-1].get_file()
    os.makedirs('user_photos', exist_ok=True)
    photo_path = f'user_photos/{user_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg'
    await photo_file.download_to_drive(photo_path)

    user_sessions[user_id].photo_path = photo_path

    processing_msg = await update.message.reply_text(
        "⏳ Провожу глубокий многоуровневый анализ...\n"
        "Это займёт 2-3 минуты.\n"
        "Я прохожу через 5 этапов: программы → род → чакры → фразы → компоновка 🔮✨"
    )

    return await process_analysis(update, context, processing_msg)


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение имени пользователя"""
    user_id = update.effective_user.id

    if user_id not in user_sessions:
        await update.message.reply_text(
            "Что-то пошло не так. Используй /start для начала."
        )
        return ConversationHandler.END

    # Сохраняем имя (берём первое слово)
    name = update.message.text.strip().split()[0]
    user_sessions[user_id].username = name
    logger.info(f"✅ Имя получено отдельно: {name}")

    # Проверяем, есть ли уже фото
    if user_sessions[user_id].photo_path:
        # Фото уже есть - запускаем анализ
        return await start_analysis(update, context, user_id)
    else:
        # Фото ещё нет - просим отправить
        await update.message.reply_text(
            "Отлично! Теперь отправь своё фото для анализа. ✨"
        )
        return WAITING_FOR_PHOTO


async def start_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> int:
    """Запуск анализа после получения имени"""
    processing_msg = await update.message.reply_text(
        "⏳ Провожу глубокий многоуровневый анализ...\n"
        "Это займёт 2-3 минуты.\n"
        "Я прохожу через 5 этапов: программы → род → чакры → фразы → компоновка 🔮✨"
    )

    return await process_analysis(update, context, processing_msg)


async def process_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE, processing_msg) -> int:
    """Выполнение анализа и отправка результата"""
    user_id = update.effective_user.id

    try:
        start_time = time.time()

        # Получаем склонения имени для замены местоимений
        logger.info(f"📝 Получаю склонения для имени: {user_sessions[user_id].username}")
        name_declensions = get_name_declensions_gpt(user_sessions[user_id].username)
        user_sessions[user_id].name_declensions = name_declensions
        logger.info(f"✅ Склонения получены: {name_declensions}")

        # Выполняем анализ
        analysis_result, usage_info = await analyze_with_metamethod(
            user_sessions[user_id].request_text,
            user_sessions[user_id].username
        )

        # Заменяем местоимения на склонённые формы имени
        logger.info("🔄 Заменяю местоимения на склонённое имя...")
        analysis_result = replace_pronouns_with_name(analysis_result, name_declensions)

        processing_time = int(time.time() - start_time)

        # Генерируем PDF
        safe_filename = f"analysis_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = generate_pdf(
            analysis_result,
            user_sessions[user_id].username,
            output_path=safe_filename
        )

        # Сохраняем в БД
        analysis_id = db.save_analysis(
            user_id=user_id,
            photo_path=user_sessions[user_id].photo_path,
            request_text=user_sessions[user_id].request_text,
            analysis_result=analysis_result,
            pdf_path=pdf_path,
            processing_time=processing_time,
            tokens_used=usage_info["total_tokens"],
            api_cost_usd=usage_info["cost_usd"],
            model_used=OPENAI_MODEL
        )

        db.save_photo_base64(analysis_id, user_sessions[user_id].photo_path)

        # Отправляем PDF
        with open(pdf_path, 'rb') as pdf_file:
            await update.message.reply_document(
                document=pdf_file,
                filename=f"Сканер_подсознания_{user_sessions[user_id].username}.pdf",
                caption="✨ Твой персональный Сканер подсознания готов!\n\n"
                        "Работай с трансформационными фразами каждый день. 🙏"
            )

        await processing_msg.delete()

        # Уменьшаем счётчик доступных сканирований
        user_sessions[user_id].scans_count -= 1

        # Очищаем файлы
        try:
            if os.path.exists(user_sessions[user_id].photo_path):
                os.remove(user_sessions[user_id].photo_path)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        except Exception as e:
            logger.warning(f"Ошибка при удалении файлов: {e}")

        # Предлагаем новый анализ
        remaining = user_sessions[user_id].scans_count
        if remaining > 0:
            keyboard = [[InlineKeyboardButton("Провести новый анализ", callback_data="new_analysis")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"У тебя осталось {remaining} сканирований.\n"
                f"Хочешь провести ещё один анализ?",
                reply_markup=reply_markup
            )

            logger.info(f"✅ Анализ #{analysis_id} завершён для {user_id} за {processing_time}с")
            # Не завершаем диалог, чтобы кнопка работала
            return WAITING_FOR_PHOTO
        else:
            keyboard = [[InlineKeyboardButton("💫 Купить ещё сканирования", url=PAYMENT_URL)]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "Это было твоё последнее доступное сканирование 🌿\n"
                "Приобрети новый пакет для продолжения работы:",
                reply_markup=reply_markup
            )

            logger.info(f"✅ Анализ #{analysis_id} завершён для {user_id} за {processing_time}с. Сканы закончились.")
            # Завершаем диалог, так как сканы закончились
            return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        await processing_msg.edit_text(
            f"❌ Произошла ошибка при анализе.\n"
            f"Попробуй ещё раз через /start\n\n"
            f"Ошибка: {str(e)}"
        )
        return ConversationHandler.END


# ===== ПРОВЕРКА БЕСПЛАТНОГО ДОСТУПА =====

async def check_free_access_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ввода почты для проверки бесплатного доступа"""
    user_id = update.effective_user.id
    email = update.message.text.strip().lower()  # Приводим к нижнему регистру

    # Показываем процесс проверки
    checking_msg = await update.message.reply_text(CHECK_ACCESS_VERIFYING)

    try:
        # Проверяем доступ через БД
        import psycopg2
        from config import POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD

        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cursor = conn.cursor()

        # Вызываем функцию проверки доступа
        cursor.execute("SELECT * FROM metaliza_check_free_access(%s)", (email,))
        result = cursor.fetchone()

        has_access, date_end, days_remaining = result

        if has_access:
            # Активируем доступ для пользователя
            cursor.execute("SELECT metaliza_activate_free_access(%s, %s)", (email, user_id))
            activated = cursor.fetchone()[0]
            conn.commit()

            if activated:
                # Форматируем дату
                date_end_formatted = date_end.strftime('%d.%m.%Y')

                # Получаем текст "после оплаты" из AFTER_PAYMENT
                after_payment_text = AFTER_PAYMENT.format(channel_link=CHANNEL_LINK).split('\n\n', 1)[1]

                # Отправляем сообщение об успехе
                await checking_msg.edit_text(
                    CHECK_ACCESS_GRANTED.format(
                        date_end=date_end_formatted,
                        days_remaining=days_remaining,
                        after_payment_text=after_payment_text
                    ),
                    parse_mode='HTML'
                )

                # Обновляем сессию
                if user_id in user_sessions:
                    user_sessions[user_id].payment_status = 'paid'
                    user_sessions[user_id].scans_count = 999999  # Безлимит
                    user_sessions[user_id].subscription_type = 'free'

                cursor.close()
                conn.close()

                return WAITING_FOR_PHOTO
            else:
                # Доступ уже был активирован ранее
                cursor.close()
                conn.close()

                keyboard = [[InlineKeyboardButton("🔄 Попробовать другую почту", callback_data='retry_email')]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await checking_msg.edit_text(
                    "⚠️ Этот доступ уже был активирован ранее",
                    reply_markup=reply_markup
                )
                return CHECKING_FREE_ACCESS
        else:
            # Доступ не найден
            cursor.close()
            conn.close()

            keyboard = [[InlineKeyboardButton("🔄 Попробовать ещё раз", callback_data='retry_email')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await checking_msg.edit_text(
                CHECK_ACCESS_NOT_FOUND,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return CHECKING_FREE_ACCESS

    except Exception as e:
        logger.error(f"Ошибка проверки доступа: {e}")
        await checking_msg.edit_text(
            f"❌ Произошла ошибка при проверке доступа.\n"
            f"Попробуйте позже или обратитесь в поддержку."
        )
        return ConversationHandler.END


async def retry_email_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Повторный запрос email"""
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(CHECK_ACCESS_START, parse_mode='HTML')
    return CHECKING_FREE_ACCESS


async def handle_checkdostup_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка текстового сообщения 'checkdostup'"""
    text = update.message.text.strip().lower()

    if text == 'checkdostup':
        user_id = update.effective_user.id
        username = update.effective_user.first_name or "Друг"

        await update.message.reply_text(CHECK_ACCESS_START, parse_mode='HTML')

        # Инициализируем сессию
        if user_id not in user_sessions:
            user_sessions[user_id] = UserSession()

        user_sessions[user_id].username = username
        user_sessions[user_id].funnel_stage = 'check_access'

        return CHECKING_FREE_ACCESS

    # Если это не checkdostup, игнорируем и остаемся в текущем состоянии
    # Просто отправим дружеское напоминание
    await update.message.reply_text(
        "Выбери один из вариантов выше, используя кнопки 👆",
        parse_mode='HTML'
    )
    return QUIZ_STATE


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()

    if query.data.startswith('quiz_'):
        return await handle_quiz_answer(update, context)
    elif query.data == 'show_welcome':
        return await show_welcome(update, context)
    elif query.data == 'about_scanner':
        return await about_scanner(update, context)
    elif query.data == 'show_examples':
        return await show_examples(update, context)
    elif query.data == 'goto_pricing':
        return await show_pricing(update, context)
    elif query.data == 'check_payment':
        return await check_payment(update, context)
    elif query.data == 'retry_email':
        return await retry_email_input(update, context)
    elif query.data == "new_analysis":
        await query.answer()
        user_id = query.from_user.id
        username = query.from_user.first_name or "Друг"

        if user_id in user_sessions:
            user_sessions[user_id].photo_path = None
            user_sessions[user_id].request_text = None
            user_sessions[user_id].username = None

        await query.message.reply_text(
            "Отлично! Начнём новый анализ. 🌟\n\n"
            "Отправь мне фото и напиши свой запрос."
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
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
        ],
        states={
            QUIZ_STATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_checkdostup_text),
                CallbackQueryHandler(button_callback),
            ],
            CHECKING_FREE_ACCESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, check_free_access_email),
                CallbackQueryHandler(button_callback),
            ],
            WAITING_FOR_PHOTO: [
                MessageHandler(filters.PHOTO, receive_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_without_photo),
                CallbackQueryHandler(button_callback),
            ],
            WAITING_FOR_REQUEST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_request),
                MessageHandler(filters.PHOTO, handle_photo_after_request),
            ],
            WAITING_FOR_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name),
                MessageHandler(filters.PHOTO, handle_photo_after_request),
            ],
            WAITING_PAYMENT: [
                CallbackQueryHandler(button_callback),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    logger.info("🤖 Мета Лиза запущена с воронкой продаж!")
    logger.info(f"📊 Модель: {OPENAI_MODEL}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
