# 🎯 Руководство по подготовке датасета для Fine-Tuning

## 📊 Что хранится в PostgreSQL

Для будущего файн-тюнинга в базе сохраняется:

- ✅ **Запрос пользователя** (`request_text`) - входные данные
- ✅ **Результат анализа** (`analysis_result`) - выходные данные
- ✅ **Фото в base64** (`photo_base64`) - для мультимодального файн-тюнинга
- ✅ **Метаданные**: токены, модель, время обработки

## 🗂 Структура данных

### Таблица `analyses`
```sql
- id: уникальный ID анализа
- user_id: ID пользователя
- request_text: текст запроса
- analysis_result: полный текст анализа от GPT
- tokens_used: количество использованных токенов
- model_used: модель (gpt-4o)
- created_at: дата создания
```

### Таблица `photos`
```sql
- id: уникальный ID
- analysis_id: связь с анализом
- photo_base64: фото в base64 формате (~23KB каждое)
```

## 📈 Когда начинать файн-тюнинг?

**Рекомендуется собрать минимум 50-100 качественных примеров.**

Текущий прогресс можно проверить:
```bash
ssh root@31.128.38.177
PGPASSWORD='kH*kyrS&9z7K' psql -h localhost -U postgres -d metamethod_bot
SELECT COUNT(*) FROM analyses WHERE LENGTH(analysis_result) > 1000;
```

## 🔧 Экспорт датасета

### 1. Используя встроенную функцию Python

```python
from database import Database

db = Database()

# Экспорт всех качественных анализов (только текст)
db.export_dataset_jsonl('dataset_for_finetuning.jsonl', min_rating=4)

# Результат: файл в формате JSONL для OpenAI Fine-Tuning API
```

### 2. Ручной экспорт из PostgreSQL

```sql
-- Экспорт в CSV
COPY (
    SELECT
        request_text as input,
        analysis_result as output,
        tokens_used,
        created_at
    FROM analyses
    WHERE LENGTH(analysis_result) > 1000
    ORDER BY created_at DESC
) TO '/tmp/metamethod_dataset.csv' CSV HEADER;
```

### 3. Экспорт с фото (мультимодальный датасет)

```sql
-- Полный датасет с фото
SELECT
    a.request_text,
    a.analysis_result,
    p.photo_base64,
    a.created_at
FROM analyses a
LEFT JOIN photos p ON a.id = p.analysis_id
WHERE LENGTH(a.analysis_result) > 1000
ORDER BY a.created_at DESC;
```

## 📝 Формат для OpenAI Fine-Tuning

### Текстовый датасет (JSONL)
```jsonl
{"messages": [{"role": "system", "content": "Ты — эксперт Мета-Метода..."}, {"role": "user", "content": "Хочу зарабатывать больше..."}, {"role": "assistant", "content": "✨ Сканер подсознания..."}]}
{"messages": [{"role": "system", "content": "Ты — эксперт Мета-Метода..."}, {"role": "user", "content": "Не получается построить отношения..."}, {"role": "assistant", "content": "✨ Сканер подсознания..."}]}
```

### Мультимодальный датасет (с изображениями)
```jsonl
{"messages": [{"role": "user", "content": [{"type": "text", "text": "Запрос..."}, {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}]}, {"role": "assistant", "content": "Анализ..."}]}
```

## 🚀 Процесс файн-тюнинга

1. **Сбор данных** (50-100 примеров) ✅ - автоматически в PostgreSQL
2. **Экспорт датасета** - используй `export_dataset_jsonl()`
3. **Валидация данных** - проверь качество примеров
4. **Загрузка в OpenAI**:
   ```bash
   openai api fine_tuning.jobs.create \
     -t dataset_for_finetuning.jsonl \
     -m gpt-4o-2024-08-06 \
     --suffix "metamethod-v1"
   ```
5. **Тестирование модели** - сравни с базовой gpt-4o
6. **Деплой** - замени `OPENAI_MODEL` в config.py на `ft:gpt-4o-...:metamethod-v1`

## 💡 Преимущества файн-тюнинга

После накопления 100+ примеров:

- 🎯 **Более точный анализ** в стиле Мета-Метода
- ⚡ **Меньше токенов** на запрос (короче промпт)
- 💰 **Дешевле** (~30-50% экономия на токенах)
- 🎨 **Консистентный стиль** во всех ответах
- 🚫 **Меньше блокировок** от OpenAI (свой файн-тюн модель)

## 📊 Мониторинг прогресса

```sql
-- Сколько собрано примеров
SELECT COUNT(*) as total_examples FROM analyses;

-- Средняя длина анализов
SELECT AVG(LENGTH(analysis_result)) as avg_length FROM analyses;

-- Распределение по темам
SELECT theme, COUNT(*)
FROM request_themes
GROUP BY theme
ORDER BY COUNT(*) DESC;
```

## 🔒 Безопасность данных

- ✅ Все данные в защищённом PostgreSQL
- ✅ Фото хранятся в base64, не на диске
- ✅ Автоматическая очистка временных файлов
- ✅ Можно анонимизировать имена перед экспортом

## 📞 Поддержка

При вопросах по файн-тюнингу обращайся к документации OpenAI:
https://platform.openai.com/docs/guides/fine-tuning
