# Архитектура БД для Воронки Продаж

## Концепция

Вместо хранения `scans_count` в памяти, храним всё в PostgreSQL:
- **Подписки** (с датами и тарифами)
- **Транзакции** (покупки)
- **Использование** (каждое сканирование = запись)
- **Бесплатный доступ** (пробный период)

---

## Схема таблиц

### 1. `users` - Пользователи

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    tg_id BIGINT UNIQUE NOT NULL,                    -- Telegram user ID
    tg_username VARCHAR(255),                         -- @username
    first_name VARCHAR(255),
    last_name VARCHAR(255),

    email VARCHAR(255),                               -- Для бесплатного доступа
    phone VARCHAR(50),                                -- Для бесплатного доступа

    current_tariff VARCHAR(50),                       -- '1scan', '3scans', 'year', 'vip', 'free', NULL
    subscription_end_date TIMESTAMP,                  -- Дата окончания подписки (для year/vip/free)

    quiz_answer VARCHAR(50),                          -- relationships/money/energy/realization
    funnel_stage VARCHAR(50),                         -- quiz/welcome/about/pricing/paid

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_tg_id ON users(tg_id);
CREATE INDEX idx_users_subscription_end ON users(subscription_end_date);
```

**Логика `current_tariff`:**
- `NULL` - не покупал ничего
- `'1scan'` - 1 сканирование (4 444₽)
- `'3scans'` - 3 сканирования (9 999₽)
- `'year'` - годовая подписка (77 777₽)
- `'vip'` - VIP подписка (199 999₽)
- `'free'` - бесплатный доступ

**Логика `subscription_end_date`:**
- `NULL` - если тариф `1scan`/`3scans` (не подписка)
- `2026-10-18` - если `year`/`vip`/`free` (подписка на период)

---

### 2. `transactions` - Покупки (история платежей)

```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(tg_id) ON DELETE CASCADE,

    tariff VARCHAR(50) NOT NULL,                      -- '1scan', '3scans', 'year', 'vip'
    amount_rub DECIMAL(10, 2),                        -- Сумма в рублях

    payment_provider VARCHAR(50),                     -- 'yookassa', 'tinkoff', 'manual', 'free'
    payment_id VARCHAR(255),                          -- ID платежа в системе
    payment_status VARCHAR(50) DEFAULT 'pending',     -- 'pending', 'paid', 'failed', 'refunded'

    scans_granted INTEGER DEFAULT 0,                  -- Сколько сканов дали (для 1scan/3scans)
    subscription_days_granted INTEGER DEFAULT 0,      -- Сколько дней дали (для year/vip/free)

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_payment_id ON transactions(payment_id);
CREATE INDEX idx_transactions_status ON transactions(payment_status);
```

**Примеры записей:**

| user_id | tariff | amount_rub | scans_granted | subscription_days_granted | payment_status |
|---------|--------|------------|---------------|---------------------------|----------------|
| 123456  | 1scan  | 4444       | 1             | 0                         | paid           |
| 123456  | year   | 77777      | 0             | 365                       | paid           |
| 789012  | free   | 0          | 0             | 7                         | paid           |

---

### 3. `scan_usage` - Использование сканов

```sql
CREATE TABLE scan_usage (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(tg_id) ON DELETE CASCADE,

    request_text TEXT NOT NULL,                       -- Текст запроса
    photo_path TEXT,                                  -- Путь к фото (или NULL если удалён)
    photo_base64 TEXT,                                -- Фото в base64 (для датасета)

    analysis_result TEXT,                             -- Результат анализа
    pdf_path TEXT,                                    -- Путь к PDF (или NULL если удалён)

    processing_time INTEGER,                          -- Время обработки в секундах
    tokens_used INTEGER,                              -- Использовано токенов
    api_cost_usd DECIMAL(10, 6),                      -- Стоимость запроса в USD
    model_used VARCHAR(50) DEFAULT 'gpt-4o',

    tariff_at_scan VARCHAR(50),                       -- Какой тариф был активен при скане

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scan_usage_user_id ON scan_usage(user_id);
CREATE INDEX idx_scan_usage_created_at ON scan_usage(created_at);
CREATE INDEX idx_scan_usage_tariff ON scan_usage(tariff_at_scan);
```

**Зачем `tariff_at_scan`?**
- Чтобы понимать, какой тариф использовал пользователь в момент скана
- Для аналитики: сколько сканов делают на каждом тарифе

---

### 4. `free_access_requests` - Заявки на бесплатный доступ

```sql
CREATE TABLE free_access_requests (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(tg_id) ON DELETE CASCADE,

    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),

    days_granted INTEGER DEFAULT 7,                   -- Сколько дней даём
    status VARCHAR(50) DEFAULT 'pending',             -- 'pending', 'approved', 'rejected', 'expired'

    approved_by BIGINT,                               -- tg_id админа, который одобрил
    rejection_reason TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    expires_at TIMESTAMP                              -- Дата окончания бесплатного доступа
);

CREATE INDEX idx_free_access_user_id ON free_access_requests(user_id);
CREATE INDEX idx_free_access_status ON free_access_requests(status);
```

**Процесс:**
1. Пользователь вводит email + phone
2. Запись создаётся со `status='pending'`
3. Админ одобряет → `status='approved'`, создаётся транзакция с `tariff='free'`
4. Обновляется `users.current_tariff='free'` и `subscription_end_date`

---

### 5. `funnel_analytics` - Аналитика воронки

```sql
CREATE TABLE funnel_analytics (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(tg_id) ON DELETE CASCADE,

    quiz_answer VARCHAR(50),                          -- relationships/money/energy/realization

    reached_welcome BOOLEAN DEFAULT FALSE,
    reached_about BOOLEAN DEFAULT FALSE,
    reached_examples BOOLEAN DEFAULT FALSE,
    reached_pricing BOOLEAN DEFAULT FALSE,
    reached_payment BOOLEAN DEFAULT FALSE,
    completed_payment BOOLEAN DEFAULT FALSE,

    first_scan_completed BOOLEAN DEFAULT FALSE,

    followup_24h_sent BOOLEAN DEFAULT FALSE,
    followup_48h_sent BOOLEAN DEFAULT FALSE,
    followup_72h_sent BOOLEAN DEFAULT FALSE,

    converted_at_stage VARCHAR(50),                   -- На каком этапе купил: pricing/24h/48h/72h

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    converted_at TIMESTAMP
);

CREATE INDEX idx_funnel_user_id ON funnel_analytics(user_id);
CREATE INDEX idx_funnel_quiz_answer ON funnel_analytics(quiz_answer);
CREATE INDEX idx_funnel_converted ON funnel_analytics(completed_payment);
```

---

## Логика работы с тарифами

### Проверка доступа к сканированию

```python
def can_user_scan(user_id: int) -> tuple[bool, str]:
    """
    Проверяет, может ли пользователь сделать скан
    Возвращает (can_scan: bool, reason: str)
    """
    user = get_user(user_id)

    # 1. Проверка подписки (year/vip/free)
    if user['current_tariff'] in ['year', 'vip', 'free']:
        if user['subscription_end_date'] and user['subscription_end_date'] > datetime.now():
            return (True, "active_subscription")
        else:
            # Подписка истекла
            update_user(user_id, current_tariff=None, subscription_end_date=None)
            return (False, "subscription_expired")

    # 2. Проверка лимитных тарифов (1scan/3scans)
    if user['current_tariff'] in ['1scan', '3scans']:
        # Считаем сколько сканов уже использовано с момента последней покупки
        last_transaction = get_last_transaction(user_id, tariff=user['current_tariff'])
        scans_used = count_scans_since(user_id, last_transaction['created_at'])
        scans_granted = last_transaction['scans_granted']

        if scans_used < scans_granted:
            return (True, f"scans_remaining_{scans_granted - scans_used}")
        else:
            # Лимит исчерпан
            update_user(user_id, current_tariff=None)
            return (False, "scans_limit_reached")

    # 3. Нет активного тарифа
    return (False, "no_active_tariff")
```

### При покупке тарифа

```python
def activate_tariff(user_id: int, tariff: str, payment_id: str):
    """Активирует тариф после оплаты"""

    tariff_config = {
        '1scan': {'scans': 1, 'days': 0, 'amount': 4444},
        '3scans': {'scans': 3, 'days': 0, 'amount': 9999},
        'year': {'scans': 0, 'days': 365, 'amount': 77777},
        'vip': {'scans': 0, 'days': 365, 'amount': 199999},
        'free': {'scans': 0, 'days': 7, 'amount': 0},
    }

    config = tariff_config[tariff]

    # 1. Создаём транзакцию
    transaction_id = create_transaction(
        user_id=user_id,
        tariff=tariff,
        amount_rub=config['amount'],
        payment_id=payment_id,
        scans_granted=config['scans'],
        subscription_days_granted=config['days'],
        payment_status='paid',
        paid_at=datetime.now()
    )

    # 2. Обновляем пользователя
    if config['days'] > 0:
        # Подписка на период
        end_date = datetime.now() + timedelta(days=config['days'])
        update_user(
            user_id,
            current_tariff=tariff,
            subscription_end_date=end_date
        )
    else:
        # Лимитный тариф (1scan/3scans)
        update_user(
            user_id,
            current_tariff=tariff,
            subscription_end_date=None
        )

    return transaction_id
```

### При использовании скана

```python
def record_scan(user_id: int, request_text: str, analysis_result: str, ...):
    """Записывает факт использования скана"""

    user = get_user(user_id)

    scan_id = create_scan_usage(
        user_id=user_id,
        request_text=request_text,
        analysis_result=analysis_result,
        tariff_at_scan=user['current_tariff'],
        ...
    )

    # Обновляем аналитику
    update_funnel_analytics(user_id, first_scan_completed=True)

    return scan_id
```

---

## Миграция существующей БД

Если у тебя уже есть таблица `users` и `analyses`:

### Вариант А: Мягкая миграция (рекомендую)

```sql
-- 1. Добавляем новые колонки в существующую таблицу users
ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS current_tariff VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_end_date TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS quiz_answer VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS funnel_stage VARCHAR(50);

-- 2. Создаём новые таблицы
CREATE TABLE transactions (...);
CREATE TABLE scan_usage (...);
CREATE TABLE free_access_requests (...);
CREATE TABLE funnel_analytics (...);

-- 3. Мигрируем данные из analyses в scan_usage
INSERT INTO scan_usage (user_id, request_text, analysis_result, photo_path, photo_base64,
                        processing_time, tokens_used, api_cost_usd, model_used,
                        tariff_at_scan, created_at)
SELECT user_id, request_text, analysis_result, photo_path, photo_base64,
       processing_time, tokens_used, api_cost_usd, model_used,
       NULL as tariff_at_scan, created_at
FROM analyses;
```

### Вариант Б: Чистая миграция

Переименовать старые таблицы и создать новые:

```sql
ALTER TABLE users RENAME TO users_old;
ALTER TABLE analyses RENAME TO analyses_old;

CREATE TABLE users (...новая структура...);
CREATE TABLE scan_usage (...);
-- и т.д.
```

---

## Преимущества этой архитектуры

### ✅ 1. Персистентность
- Данные не теряются при перезапуске бота
- `user_sessions` в памяти нужен только для текущего диалога

### ✅ 2. История
- Видно всю историю покупок (`transactions`)
- Видно каждое использование скана (`scan_usage`)

### ✅ 3. Гибкость тарифов
- Легко добавить новый тариф
- Легко изменить логику (например, дать безлимит на месяц)

### ✅ 4. Аналитика
- Конверсия по этапам воронки
- Популярность сфер квиза
- Средний чек
- Retention (сколько сканов делают на каждом тарифе)

### ✅ 5. Бесплатный доступ
- Отдельная таблица с модерацией
- Можно дать пробный период вручную

### ✅ 6. Масштабируемость
- Готово к рефералке (добавить `referrer_id` в `users`)
- Готово к промокодам (добавить `promo_code` в `transactions`)
- Готово к подаркам (добавить `gifted_by` в `transactions`)

---

## Что дальше?

Я предлагаю:

1. **Создать SQL-миграцию** - файл с созданием всех таблиц
2. **Обновить `database.py`** - добавить методы для работы с новыми таблицами
3. **Интегрировать в бота** - использовать БД вместо `user_sessions` для тарифов
4. **Добавить админ-панель** (опционально) - для модерации бесплатного доступа

Согласна с этой архитектурой? Что-то добавить или изменить?
