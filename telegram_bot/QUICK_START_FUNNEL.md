# Быстрый старт: Воронка Продаж

## Что реализовано ✅

1. **Мини-квиз** при /start по 4 сферам:
   - 💕 Отношения
   - 💰 Деньги
   - ⚡ Энергия
   - 🎯 Реализация

2. **8 этапов воронки:**
   - Квиз → Адаптированный пример → Приветствие → Описание → Примеры → Тарифы → Оплата → Работа

3. **Автоматические дожимы** через 24/48/72 часа для неоплативших

4. **Проверка оплаты** и лимиты сканирований

5. **Полная логика сканера** после оплаты (фото + текст → PDF)

---

## Файлы

- **`sales_funnel_texts.py`** - все тексты сообщений
- **`bot_with_sales_funnel.py`** - основной бот с воронкой
- **`SALES_FUNNEL_README.md`** - полная документация (читай обязательно!)

---

## Что нужно добавить перед запуском

### 1. Медиафайлы (ОБЯЗАТЕЛЬНО)

Создай папку `media/` и добавь:

```
media/
├── chakras_photo.jpg              # Фото по 7 чакрам
├── pricing_presentation.jpg       # Продающая презентация
├── examples/
│   ├── example1.jpg
│   ├── example2.jpg
│   └── example3.jpg
├── quiz_examples/
│   ├── relationships.pdf
│   ├── money.pdf
│   ├── energy.pdf
│   └── realization.pdf
└── voice/
    └── liza_promo.ogg            # Голосовое от Лизы
```

**Где добавить код отправки:**

1. Фото чакр - строка 142 в `bot_with_sales_funnel.py`
2. Презентация - строка 198
3. Примеры - строки 170-172
4. PDF квиза - строка 131
5. Голосовое - строка 132

### 2. Ссылка на канал

В `sales_funnel_texts.py` строка 174:

```python
CHANNEL_LINK = "https://t.me/+ВАШ_ИНВАЙТ_ЛИНК"
```

### 3. Интеграция оплаты (КРИТИЧНО!)

**Сейчас:** Всем даёт доступ для теста (строка 239)

**Нужно:** Интегрировать Yookassa/Tinkoff

Смотри раздел "TODO: Интеграция" → "Проверка оплаты" в [SALES_FUNNEL_README.md](SALES_FUNNEL_README.md)

---

## Локальный тест

```bash
cd "/Users/daniillepekhin/My Python/Natalie Zemskova/telegram_bot"
python3 bot_with_sales_funnel.py
```

**Тестовый сценарий:**

1. `/start` → выбери сферу в квизе
2. Пройди всю воронку до тарифов
3. Нажми "Я оплатил" (автоматически даст доступ)
4. Отправь фото + текст запроса
5. Получи PDF
6. Проверь, что счётчик сканирований уменьшился

---

## Деплой на сервер

```bash
# 1. Загрузить файлы
scp sales_funnel_texts.py root@31.128.38.177:/opt/Natalie_Zemskova/
scp bot_with_sales_funnel.py root@31.128.38.177:/opt/Natalie_Zemskova/

# 2. Загрузить медиафайлы
scp -r media/ root@31.128.38.177:/opt/Natalie_Zemskova/

# 3. Подключиться к серверу
ssh root@31.128.38.177

# 4. Изменить systemd service
nano /etc/systemd/system/natalie-bot.service

# Заменить строку ExecStart на:
ExecStart=/opt/Natalie_Zemskova/venv/bin/python3 /opt/Natalie_Zemskova/bot_with_sales_funnel.py

# 5. Перезапустить
systemctl daemon-reload
systemctl restart natalie-bot.service
systemctl status natalie-bot.service
```

---

## Важно! ⚠️

### 1. Дожимы не персистентные
При перезапуске бота таймеры дожимов сбрасываются. Для продакшена нужно:
- Использовать Celery + Redis
- Или сохранять `next_followup_at` в БД

### 2. Состояние платежа в памяти
`user_sessions` теряется при перезапуске. Добавь в БД:
```sql
ALTER TABLE users ADD COLUMN payment_status TEXT;
ALTER TABLE users ADD COLUMN scans_remaining INTEGER;
```

### 3. Проверка оплаты = заглушка
Сейчас всем даёт доступ. **Обязательно** интегрируй реальную проверку!

---

## Следующие шаги

1. ✅ Код воронки готов
2. ⏳ Добавить медиафайлы
3. ⏳ Записать голосовое от Лизы
4. ⏳ Интегрировать оплату (Yookassa)
5. ⏳ Протестировать локально
6. ⏳ Задеплоить на сервер
7. ⏳ Настроить аналитику конверсии

---

## Помощь

Вся детальная информация в [SALES_FUNNEL_README.md](SALES_FUNNEL_README.md):
- Полная логика воронки
- Примеры интеграции платежей
- Структура UserSession
- SQL для аналитики
- И многое другое

Если что-то непонятно — пиши!
