# Инструкция: Бесплатный доступ к Сканеру

## Как это работает

1. Ты добавляешь записи в таблицу `metaliza_free_access` с email и датой окончания доступа
2. Пользователь переходит по ссылке `https://t.me/skanermetalizabot?start=checkdostup`
3. Бот просит ввести email
4. Проверяет в БД наличие активного доступа
5. Если найдено → активирует доступ для этого пользователя
6. Если не найдено → показывает ошибку

---

## Как добавить бесплатный доступ

### Вариант 1: SQL-запрос (рекомендую)

Подключись к базе `metamethod_bot` и выполни:

```sql
INSERT INTO metaliza_free_access (email, phone, date_end, created_by, note)
VALUES
    ('ivanov@mail.ru', '+79001234567', NOW() + INTERVAL '7 days', 'manual', 'Промо-акция Октябрь'),
    ('petrov@gmail.com', NULL, NOW() + INTERVAL '14 days', 'manual', 'Приз в конкурсе'),
    ('sidorova@yandex.ru', '+79119876543', NOW() + INTERVAL '30 days', 'manual', 'VIP-клиент');
```

**Параметры:**
- `email` - почта в **НИЖНЕМ** регистре (будет автоматически приведена)
- `phone` - телефон (опционально, можно `NULL`)
- `date_end` - до какой даты доступ (используй `NOW() + INTERVAL '7 days'` для 7 дней)
- `created_by` - кто выдал доступ (например, 'manual', 'promo', 'admin')
- `note` - примечание (откуда пришёл, причина)

### Вариант 2: Через SSH на сервере

```bash
ssh root@31.128.38.177

PGPASSWORD='kH*kyrS&9z7K' psql -h localhost -U postgres -d metamethod_bot

INSERT INTO metaliza_free_access (email, date_end, created_by, note)
VALUES ('test@example.com', NOW() + INTERVAL '7 days', 'manual', 'Тестовый доступ');

\q
```

---

## Проверка добавленных доступов

```sql
-- Все активные доступы
SELECT
    email,
    phone,
    date_end,
    EXTRACT(DAY FROM (date_end - NOW()))::INTEGER as days_remaining,
    activated_at,
    user_id,
    note
FROM metaliza_free_access
WHERE is_active = TRUE
  AND date_end > NOW()
ORDER BY date_end;

-- Все доступы (включая активированные и истёкшие)
SELECT * FROM metaliza_free_access ORDER BY created_at DESC LIMIT 20;
```

---

## Проверка доступа через SQL-функцию

```sql
-- Проверить есть ли доступ для конкретной почты
SELECT * FROM metaliza_check_free_access('test@example.com');

-- Результат:
-- has_access | date_end            | days_remaining
-- TRUE       | 2025-10-25 12:00:00 | 7
```

---

## Как пользователь активирует доступ

1. Переходит по ссылке: `https://t.me/skanermetalizabot?start=checkdostup`

2. Бот отправляет:
   ```
   Введи свою электронную почту, чтобы мы могли продолжить 🙌🏻

   Бот сверит и откроет доступ к сканеру 🤍
   ```

3. Пользователь вводит: `test@example.com`

4. Бот проверяет и если доступ найден:
   ```
   ✅ Отлично! Твой доступ подтверждён 🤍

   Доступ к Сканеру активен до: 25.10.2025
   Осталось дней: 7

   [Инструкция как пользоваться]
   ```

5. После активации:
   - Записывается `user_id` (привязка к Telegram аккаунту)
   - Записывается `activated_at` (дата активации)
   - Обновляется `metaliza_users.current_tariff = 'free'`
   - Обновляется `metaliza_users.subscription_end_date`

---

## Частые сценарии

### Дать доступ на 7 дней

```sql
INSERT INTO metaliza_free_access (email, date_end, created_by, note)
VALUES ('user@example.com', NOW() + INTERVAL '7 days', 'manual', 'Промо 7 дней');
```

### Дать доступ на месяц

```sql
INSERT INTO metaliza_free_access (email, date_end, created_by, note)
VALUES ('vip@example.com', NOW() + INTERVAL '30 days', 'manual', 'VIP месяц');
```

### Массовая выдача (например, список из 10 человек)

```sql
INSERT INTO metaliza_free_access (email, date_end, created_by, note)
VALUES
    ('user1@mail.ru', NOW() + INTERVAL '7 days', 'promo_oct', 'Акция Октябрь'),
    ('user2@mail.ru', NOW() + INTERVAL '7 days', 'promo_oct', 'Акция Октябрь'),
    ('user3@gmail.com', NOW() + INTERVAL '7 days', 'promo_oct', 'Акция Октябрь'),
    ('user4@yandex.ru', NOW() + INTERVAL '7 days', 'promo_oct', 'Акция Октябрь'),
    ('user5@gmail.com', NOW() + INTERVAL '7 days', 'promo_oct', 'Акция Октябрь');
    -- ... и так далее
```

### Продлить доступ существующему пользователю

```sql
-- Найти email пользователя
SELECT email, date_end FROM metaliza_free_access WHERE user_id = 123456;

-- Продлить на 7 дней
UPDATE metaliza_free_access
SET date_end = date_end + INTERVAL '7 days',
    updated_at = NOW()
WHERE email = 'user@example.com';
```

### Отозвать доступ

```sql
UPDATE metaliza_free_access
SET is_active = FALSE,
    updated_at = NOW()
WHERE email = 'user@example.com';
```

---

## Логи и мониторинг

### Кто активировал доступ за последние 24 часа

```sql
SELECT
    email,
    user_id,
    activated_at,
    note
FROM metaliza_free_access
WHERE activated_at > NOW() - INTERVAL '24 hours'
ORDER BY activated_at DESC;
```

### Сколько дней осталось у активных подписок

```sql
SELECT
    email,
    EXTRACT(DAY FROM (date_end - NOW()))::INTEGER as days_left,
    date_end
FROM metaliza_free_access
WHERE is_active = TRUE
  AND date_end > NOW()
  AND user_id IS NOT NULL
ORDER BY days_left;
```

### Истекающие доступы (меньше 3 дней)

```sql
SELECT
    email,
    user_id,
    EXTRACT(DAY FROM (date_end - NOW()))::INTEGER as days_left,
    date_end
FROM metaliza_free_access
WHERE is_active = TRUE
  AND date_end > NOW()
  AND date_end < NOW() + INTERVAL '3 days'
ORDER BY date_end;
```

---

## Ошибки и решения

### "Я не вижу вашего доступа"

**Причины:**
1. Email введён с ошибкой
2. Email не добавлен в таблицу
3. Доступ истёк (`date_end < NOW()`)
4. Доступ деактивирован (`is_active = FALSE`)

**Решение:**
```sql
-- Проверить наличие
SELECT * FROM metaliza_free_access WHERE email = 'test@example.com';

-- Если нет - добавить
INSERT INTO metaliza_free_access (email, date_end)
VALUES ('test@example.com', NOW() + INTERVAL '7 days');
```

### "Этот доступ уже был активирован ранее"

**Причина:** Пользователь уже активировал этот email ранее (`user_id IS NOT NULL`)

**Решение:**
Если нужно дать доступ повторно - продли дату:
```sql
UPDATE metaliza_free_access
SET date_end = NOW() + INTERVAL '7 days',
    updated_at = NOW()
WHERE email = 'test@example.com';
```

Или создай новую запись с другим email.

---

## Автоматизация (для будущего)

Можно создать скрипт для массовой выдачи из CSV:

```python
import csv
import psycopg2

conn = psycopg2.connect(...)
cursor = conn.cursor()

with open('free_access_list.csv', 'r') as f:
    reader = csv.DictReader(f)  # email,phone,days,note
    for row in reader:
        cursor.execute("""
            INSERT INTO metaliza_free_access (email, phone, date_end, created_by, note)
            VALUES (%s, %s, NOW() + INTERVAL '%s days', 'csv_import', %s)
        """, (row['email'], row['phone'], row['days'], row['note']))

conn.commit()
```

---

## Важно

1. **Email всегда в нижнем регистре** - бот автоматически приводит к `lower()`, БД тоже
2. **Одна почта = одна запись** - нельзя добавить дубликат (`UNIQUE` constraint)
3. **Привязка к Telegram** происходит при активации - до этого `user_id = NULL`
4. **Истёкшие доступы** автоматически не удаляются - остаются в БД для статистики

---

## Ссылка для пользователей

**Отправляй эту ссылку тем, кому выдал доступ:**

```
https://t.me/skanermetalizabot?start=checkdostup
```

Или делай QR-код для офлайн мероприятий.
