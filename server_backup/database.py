"""
Модуль для работы с PostgreSQL базой данных
Сохраняет все анализы для подготовки датасета
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import base64
from config import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD
)
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        """Подключение к PostgreSQL"""
        try:
            self.connection = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD
            )
            logger.info("✅ Подключение к PostgreSQL успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к PostgreSQL: {e}")
            raise

    def execute(self, query, params=None, fetch=False):
        """Выполнение SQL запроса"""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if fetch:
                    result = cursor.fetchall()
                    self.connection.commit()
                    return result
                self.connection.commit()
                return cursor.rowcount
        except Exception as e:
            self.connection.rollback()
            logger.error(f"❌ Ошибка выполнения запроса: {e}")
            raise

    def create_or_update_user(self, user_id, username=None, first_name=None, last_name=None):
        """Создать или обновить пользователя"""
        query = """
            INSERT INTO users (user_id, username, first_name, last_name)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                last_active = CURRENT_TIMESTAMP
        """
        self.execute(query, (user_id, username, first_name, last_name))
        logger.info(f"✅ Пользователь {user_id} ({first_name}) сохранён")

    def save_analysis(self, user_id, photo_path, request_text, analysis_result,
                     pdf_path, processing_time, tokens_used, model_used):
        """Сохранить анализ в БД"""
        query = """
            INSERT INTO analyses
            (user_id, photo_path, request_text, analysis_result, pdf_path,
             processing_time_seconds, tokens_used, model_used)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        result = self.execute(
            query,
            (user_id, photo_path, request_text, analysis_result, pdf_path,
             processing_time, tokens_used, model_used),
            fetch=True
        )
        analysis_id = result[0]['id']
        logger.info(f"✅ Анализ #{analysis_id} сохранён для пользователя {user_id}")
        return analysis_id

    def save_photo_base64(self, analysis_id, photo_path):
        """Сохранить фото в base64 для датасета"""
        try:
            with open(photo_path, 'rb') as f:
                photo_bytes = f.read()
                photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')
                photo_size_kb = len(photo_bytes) // 1024

            query = """
                INSERT INTO photos (analysis_id, photo_base64, photo_size_kb)
                VALUES (%s, %s, %s)
            """
            self.execute(query, (analysis_id, photo_base64, photo_size_kb))
            logger.info(f"✅ Фото для анализа #{analysis_id} сохранено ({photo_size_kb} KB)")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения фото: {e}")

    def get_user_stats(self, user_id):
        """Получить статистику пользователя"""
        query = """
            SELECT user_id, username, first_name, created_at, last_active, total_analyses
            FROM users
            WHERE user_id = %s
        """
        result = self.execute(query, (user_id,), fetch=True)
        return result[0] if result else None

    def get_recent_analyses(self, limit=10):
        """Получить последние анализы"""
        query = """
            SELECT a.id, a.user_id, u.first_name, a.request_text, a.created_at,
                   a.tokens_used, a.model_used, a.is_approved_for_dataset
            FROM analyses a
            JOIN users u ON a.user_id = u.user_id
            ORDER BY a.created_at DESC
            LIMIT %s
        """
        return self.execute(query, (limit,), fetch=True)

    def get_analytics_summary(self, days=7):
        """Получить аналитику за последние N дней"""
        query = f"""
            SELECT * FROM analytics_summary
            WHERE date >= CURRENT_DATE - INTERVAL '{days} days'
            ORDER BY date DESC
        """
        return self.execute(query, fetch=True)

    def get_dataset_ready(self, limit=100):
        """Получить готовые данные для датасета"""
        query = """
            SELECT * FROM dataset_ready
            LIMIT %s
        """
        return self.execute(query, (limit,), fetch=True)

    def approve_for_dataset(self, analysis_id, quality_rating, notes=None):
        """Одобрить анализ для датасета"""
        query = """
            UPDATE analyses
            SET is_approved_for_dataset = TRUE,
                quality_rating = %s,
                dataset_notes = %s
            WHERE id = %s
        """
        self.execute(query, (quality_rating, notes, analysis_id))
        logger.info(f"✅ Анализ #{analysis_id} одобрен для датасета (рейтинг: {quality_rating})")

    def save_feedback(self, analysis_id, user_id, rating, comment=None):
        """Сохранить отзыв пользователя"""
        query = """
            INSERT INTO feedback (analysis_id, user_id, rating, comment)
            VALUES (%s, %s, %s, %s)
        """
        self.execute(query, (analysis_id, user_id, rating, comment))
        logger.info(f"✅ Отзыв для анализа #{analysis_id}: {rating}/5")

    def get_theme_statistics(self):
        """Статистика по темам запросов"""
        query = """
            SELECT theme, COUNT(*) as count
            FROM request_themes
            GROUP BY theme
            ORDER BY count DESC
        """
        return self.execute(query, fetch=True)

    def export_dataset_jsonl(self, output_file='dataset_export.jsonl', min_rating=4):
        """Экспорт датасета в JSONL для fine-tuning"""
        query = """
            SELECT
                a.request_text,
                a.analysis_result,
                p.photo_base64
            FROM analyses a
            LEFT JOIN photos p ON a.id = p.analysis_id
            WHERE a.is_approved_for_dataset = TRUE
              AND a.quality_rating >= %s
            ORDER BY a.created_at DESC
        """
        results = self.execute(query, (min_rating,), fetch=True)

        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            for row in results:
                data = {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": row['request_text']},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{row['photo_base64']}"
                                    }
                                }
                            ]
                        },
                        {
                            "role": "assistant",
                            "content": row['analysis_result']
                        }
                    ]
                }
                f.write(json.dumps(data, ensure_ascii=False) + '\n')

        logger.info(f"✅ Датасет экспортирован: {len(results)} записей → {output_file}")
        return len(results)

    def close(self):
        """Закрыть соединение"""
        if self.connection:
            self.connection.close()
            logger.info("🔌 Соединение с PostgreSQL закрыто")


# Singleton для глобального доступа
_db_instance = None

def get_db():
    """Получить глобальный экземпляр БД"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
