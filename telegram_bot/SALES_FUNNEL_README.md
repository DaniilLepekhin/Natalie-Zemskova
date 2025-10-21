# Воронка Продаж для Сканера Подсознания

## Обзор

Реализована полная воронка продаж с:
- **Мини-квизом** по 4 сферам жизни
- **8 этапами коммуникации** (приветствие → квиз → описание → примеры → тарифы → оплата → работа → дожимы)
- **Автоматическими дожимами** через 24/48/72 часа
- **Проверкой оплаты** и лимитом сканирований

---

## Файловая структура

### 1. `sales_funnel_texts.py`
Все тексты сообщений воронки:
- `QUIZ_MESSAGE` - Мини-квиз "Что у тебя в фокусе?"
- `QUIZ_OPTIONS` - 4 кнопки: Отношения/Деньги/Энергия/Реализация
- `QUIZ_EXAMPLES` - Адаптированные примеры под каждую сферу
- `WELCOME_MESSAGE` - Приветствие от Мета Лизы
- `ABOUT_SCANNER` - Описание сканера
- `EXAMPLES_MESSAGE` - Примеры сканирований
- `PRICING_MESSAGE` - 4 тарифа
- `AFTER_PAYMENT` - Инструкции после оплаты
- `FOLLOWUP_24H/48H/72H` - Дожимы

### 2. `bot_with_sales_funnel.py`
Основной бот с воронкой продаж:
- Мини-квиз в начале
- Состояния: `QUIZ_STATE`, `WAITING_FOR_PHOTO`, `WAITING_FOR_REQUEST`, `WAITING_PAYMENT`, `PAID_USER`
- Автодожимы через asyncio
- Проверка оплаты и лимитов

---

## Логика воронки (8 этапов)

### Этап 0: Мини-квиз (при /start)

**Цель:** Персонализация + вовлечение

```
Пользователь: /start
Бот: "Что у тебя сейчас в фокусе? 🌟"
     [💕 Отношения] [💰 Деньги] [⚡ Энергия] [🎯 Реализация]
```

**Что происходит:**
1. Бот сохраняет выбор сферы в `user_sessions[user_id].quiz_answer`
2. Показывает адаптированный пример из `QUIZ_EXAMPLES[сфера]`
3. Отправляет пример PDF по выбранной теме (TODO: добавить файлы)
4. Кнопка: "✨ Узнать про Сканер подробнее"

---

### Этап 1: Приветствие

**Триггер:** Нажатие "Узнать про Сканер"

```
Привет 🌿 Я - Мета Лиза...
[Да, хочу пройти сканирование] → (Тарифы)
[Хочу узнать подробнее] → (Описание)
```

---

### Этап 2: Что такое Сканер?

**Триггер:** Кнопка "Хочу узнать подробнее"

```
Сканер Подсознания — это метод диагностики...
– распознать блоки
– увидеть утечки энергии
– получить ясность

[📂 Посмотреть примеры] → (Примеры)
[⚡ Пройти сканирование] → (Тарифы)
```

**TODO:** Отправить фото по 7 чакрам (закомментировано на строке 142)

---

### Этап 3: Примеры

**Триггер:** Кнопка "Посмотреть примеры"

```
Вот примеры реальных сканирований 👇
[скрины PDF]

[✨ Хочу своё сканирование] → (Тарифы)
```

**TODO:** Добавить 3-5 скринов примеров (строки 170-172)

---

### Этап 4: Тарифы

**Триггер:** Любая кнопка "Пройти сканирование" / "Хочу сканирование"

```
Выбери свой формат диагностики 👇
1️⃣ 1 Сканирование — 4 444 ₽
2️⃣ 3 Сканирования — 9 999 ₽
3️⃣ Подписка на год — 77 777 ₽
4️⃣ ВИП-подписка — 199 999 ₽

[💫 Перейти к оплате] → https://lizaperman.online/scaner_fullpay
[🔙 Вернуться к описанию]
```

**TODO:** Добавить продающую презентацию (строка 198)

---

### Этап 5: Проверка оплаты

**Триггер:** Кнопка "✅ Я оплатил"

```
⏳ Проверяю статус оплаты...

ЕСЛИ ОПЛАЧЕНО:
  "Поздравляю 💫 Твоё Сканирование начнется прямо сейчас🌀"
  → Переход к работе со сканером (WAITING_FOR_PHOTO)

ЕСЛИ НЕ ОПЛАЧЕНО:
  "❌ Оплата не найдена. Попробуй через минуту"
  [Попробовать снова]
```

**Текущая логика:**
- Строки 211-273 в `bot_with_sales_funnel.py`
- **ВРЕМЕННО:** Всем даёт доступ для тестирования (`payment_verified = True`)
- **TODO:** Интеграция с Yookassa/Tinkoff API

---

### Этап 6: После оплаты (работа со сканером)

**Состояние:** `WAITING_FOR_PHOTO` → `WAITING_FOR_REQUEST`

Логика идентична оригинальному боту:
1. Пользователь отправляет фото (с подписью или без)
2. Если без подписи → бот просит текст
3. Запускается анализ через `analyze_with_metamethod()`
4. Генерируется PDF
5. Отправляется пользователю

**Отличие:** Счётчик сканирований

```python
user_sessions[user_id].scans_count -= 1  # Уменьшается после каждого анализа

if remaining > 0:
    "У тебя осталось {remaining} сканирований"
    [Провести новый анализ]
else:
    "Это было твоё последнее сканирование"
    [💫 Купить ещё] → payment_url
```

---

### Этапы 7-8: Автоматические дожимы

**Функция:** `schedule_followups()` (строки 276-340)

#### Дожим 1 (через 24 часа)

```
Привет 🌿 Напоминаю, что ты можешь пройти Сканер...
"Это как будто кто-то наконец объяснил, что со мной происходит" ✨

[👉 Пройти Сканирование]
```

**Условие:** `payment_status != 'paid'`

#### Дожим 2 (через 48 часов)

```
Иногда мы ищем ответы снаружи… Но Сканер показывает — всё уже внутри.

[👉 Начать Сканирование]
```

**Условие:** `payment_status != 'paid'`

#### Дожим 3 (через 72 часа)

```
Благодарю, что была в этом поле 💫
Пока ты откладываешь, твои программы продолжают работать.

[👉 Перейти к Сканеру]
```

**Условие:** `payment_status != 'paid'`

**Технология:**
- Используется `asyncio.create_task()` при старте пользователя
- Каждый дожим проверяет статус оплаты перед отправкой
- Если пользователь оплатил — дожимы прекращаются

---

## UserSession структура

```python
class UserSession:
    photo_path = None              # Путь к загруженному фото
    request_text = None            # Текст запроса
    username = None                # Имя пользователя
    start_time = None              # Время начала сессии
    quiz_answer = None             # Выбор в квизе: relationships/money/energy/realization
    payment_status = None          # None / 'pending' / 'paid'
    funnel_stage = 'start'         # Этап воронки
    last_funnel_message_time = None  # Время последнего сообщения
    scans_count = 0                # Количество доступных сканирований
    subscription_type = None       # '1scan' / '3scans' / 'year' / 'vip'
```

---

## Состояния ConversationHandler

1. **QUIZ_STATE** - Квиз и вся воронка до оплаты
2. **WAITING_PAYMENT** - Ожидание подтверждения оплаты
3. **WAITING_FOR_PHOTO** - Ожидание фото (после оплаты)
4. **WAITING_FOR_REQUEST** - Ожидание текста запроса
5. **PAID_USER** - Оплативший пользователь (резерв)

---

## TODO: Интеграция

### 1. Медиафайлы

Добавить в папку `/telegram_bot/media/`:

```
media/
├── chakras_photo.jpg           # Фото по 7 чакрам (строка 142)
├── pricing_presentation.jpg    # Продающая презентация (строка 198)
├── examples/
│   ├── example1.jpg           # Пример сканирования 1
│   ├── example2.jpg           # Пример сканирования 2
│   └── example3.jpg           # Пример сканирования 3
├── quiz_examples/
│   ├── relationships.pdf      # Пример по отношениям
│   ├── money.pdf             # Пример по деньгам
│   ├── energy.pdf            # Пример по энергии
│   └── realization.pdf       # Пример по реализации
└── voice/
    └── liza_promo.ogg        # Голосовое от Лизы с продажей
```

### 2. Голосовое от Лизы

**Где добавить:** После квиза или в описании сканера

```python
# В функции handle_quiz_answer() после строки 130:
await query.message.reply_voice(
    voice=open('media/voice/liza_promo.ogg', 'rb'),
    caption="Послушай, что говорит Лиза о Сканере 💫"
)
```

**Что говорить в голосовом:**
- Приветствие от Лизы
- Краткое описание Мета-Метода
- Результаты участниц
- Призыв к действию (пройти сканирование)

### 3. Проверка оплаты (КРИТИЧНО!)

**Текущий код (строка 239):**
```python
# ВРЕМЕННО: даём доступ всем
payment_verified = True
```

**Нужно заменить на:**

#### Вариант А: Yookassa (рекомендую)

```python
from yookassa import Configuration, Payment

Configuration.account_id = 'ваш_shopId'
Configuration.secret_key = 'ваш_secretKey'

def check_payment_yookassa(user_id):
    # Ищем платёж по metadata.user_id
    payments = Payment.list({"status": "succeeded"})

    for payment in payments.items:
        if payment.metadata.get('user_id') == str(user_id):
            return True
    return False

# В функции check_payment():
payment_verified = check_payment_yookassa(user_id)
```

#### Вариант Б: Tinkoff

```python
import requests

def check_payment_tinkoff(user_id):
    url = "https://securepay.tinkoff.ru/v2/GetState"
    data = {
        "TerminalKey": "ваш_ключ",
        "OrderId": f"user_{user_id}"
    }
    response = requests.post(url, json=data)
    result = response.json()
    return result.get('Status') == 'CONFIRMED'
```

#### Вариант В: Webhook от платёжки

1. Создать endpoint `/webhook/payment`
2. Платёжная система отправляет POST при успешной оплате
3. Обновляем `user_sessions[user_id].payment_status = 'paid'`

```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook/payment', methods=['POST'])
def payment_webhook():
    data = request.json
    user_id = data['metadata']['user_id']

    if user_id in user_sessions:
        user_sessions[user_id].payment_status = 'paid'
        user_sessions[user_id].scans_count = get_scans_by_tariff(data['amount'])

    return {"status": "ok"}
```

### 4. Установка лимита сканирований

**Текущий код (строка 245):**
```python
user_sessions[user_id].scans_count = 1  # По умолчанию
```

**Нужно:**
```python
def get_scans_by_amount(amount_rub):
    """Определяет количество сканирований по сумме оплаты"""
    if amount_rub >= 199999:
        return 999999  # ВИП - безлимит
    elif amount_rub >= 77777:
        return 999999  # Год - безлимит
    elif amount_rub >= 9999:
        return 3
    elif amount_rub >= 4444:
        return 1
    else:
        return 0

# При проверке оплаты:
amount = payment_data['amount']['value']  # из Yookassa
user_sessions[user_id].scans_count = get_scans_by_amount(amount)
```

### 5. Ссылка на канал

**Заменить в `sales_funnel_texts.py` строка 174:**
```python
CHANNEL_LINK = "https://t.me/+ВАША_ССЫЛКА"  # TODO
```

На реальную ссылку приглашения в канал.

---

## Запуск

### Локально (для теста)

```bash
cd "/Users/daniillepekhin/My Python/Natalie Zemskova/telegram_bot"
python3 bot_with_sales_funnel.py
```

### На сервере

1. Заменить `bot_with_db.py` на `bot_with_sales_funnel.py`:

```bash
scp bot_with_sales_funnel.py root@31.128.38.177:/opt/Natalie_Zemskova/bot_with_sales_funnel.py
scp sales_funnel_texts.py root@31.128.38.177:/opt/Natalie_Zemskova/sales_funnel_texts.py
```

2. Обновить systemd service:

```bash
ssh root@31.128.38.177

# Изменить ExecStart в /etc/systemd/system/natalie-bot.service
ExecStart=/opt/Natalie_Zemskova/venv/bin/python3 /opt/Natalie_Zemskova/bot_with_sales_funnel.py

systemctl daemon-reload
systemctl restart natalie-bot.service
```

---

## Тестирование

### Сценарий 1: Полная воронка без оплаты

1. `/start` → квиз
2. Выбрать сферу (например, "💰 Деньги")
3. Увидеть адаптированный пример
4. "Узнать про Сканер" → приветствие
5. "Хочу узнать подробнее" → описание
6. "Посмотреть примеры" → примеры
7. "Хочу сканирование" → тарифы
8. НЕ оплачивать
9. Через 24 часа → получить дожим 1
10. Через 48 часов → получить дожим 2
11. Через 72 часа → получить дожим 3

### Сценарий 2: Быстрая покупка

1. `/start` → квиз → выбрать сферу
2. "Узнать про Сканер"
3. "Да, хочу пройти" → тарифы
4. "Перейти к оплате" → оплатить
5. "Я оплатил" → доступ к сканеру
6. Отправить фото и запрос
7. Получить PDF
8. "Провести новый анализ" → отправить ещё фото
9. Если лимит исчерпан → предложение купить ещё

### Сценарий 3: Оплата после дожима

1. `/start` → пройти до тарифов
2. НЕ оплачивать
3. Через 24ч получить дожим
4. Нажать кнопку в дожиме → тарифы
5. Оплатить → получить доступ

---

## Метрики для отслеживания

Добавить в БД таблицу `funnel_analytics`:

```sql
CREATE TABLE funnel_analytics (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    quiz_answer TEXT,           -- relationships/money/energy/realization
    funnel_stage TEXT,          -- quiz/welcome/about/examples/pricing/paid
    button_clicked TEXT,        -- название кнопки
    reached_payment BOOLEAN,    -- дошёл до оплаты?
    completed_payment BOOLEAN,  -- оплатил?
    followup_sent_24h BOOLEAN,  -- отправлен дожим 24ч?
    followup_sent_48h BOOLEAN,  -- отправлен дожим 48ч?
    followup_sent_72h BOOLEAN,  -- отправлен дожим 72ч?
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Для анализа конверсии:
- Сколько % проходят квиз
- Какая сфера выбирается чаще
- На каком этапе отваливаются
- Эффективность дожимов (% оплаты после каждого)

---

## Важные замечания

1. **Дожимы работают в памяти:** Если бот перезапустится, таймеры сбросятся. Для продакшена использовать:
   - Celery + Redis для отложенных задач
   - Или сохранять `followup_scheduled_at` в БД и проверять при старте

2. **Состояние платежа не персистентное:** При перезапуске бота все `user_sessions` теряются. Нужно сохранять в БД:
```sql
ALTER TABLE users ADD COLUMN payment_status TEXT;
ALTER TABLE users ADD COLUMN scans_remaining INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN subscription_type TEXT;
```

3. **Безопасность:** Не хардкодить ключи платёжных систем в коде. Использовать переменные окружения.

---

## Следующие шаги

1. ✅ Структура воронки создана
2. ✅ Мини-квиз реализован
3. ✅ Автодожимы через asyncio
4. ⏳ Добавить медиафайлы (фото, PDF примеры, голосовое)
5. ⏳ Интегрировать проверку оплаты (Yookassa/Tinkoff)
6. ⏳ Протестировать на реальных пользователях
7. ⏳ Настроить аналитику конверсии
8. ⏳ Сделать персистентность состояний в БД
