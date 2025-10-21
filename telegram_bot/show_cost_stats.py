#!/usr/bin/env python3
"""
Скрипт для просмотра статистики по стоимости API запросов
"""

import psycopg2
from tabulate import tabulate

DB_CONFIG = {
    'host': 'localhost',
    'database': 'metamethod_bot',
    'user': 'postgres',
    'password': 'kH*kyrS&9z7K'
}

def get_db():
    return psycopg2.connect(**DB_CONFIG)

def show_total_stats():
    """Общая статистика"""
    conn = get_db()
    cur = conn.cursor()

    query = """
        SELECT
            COUNT(*) as total_analyses,
            COALESCE(SUM(api_cost_usd), 0) as total_cost_usd,
            COALESCE(AVG(api_cost_usd), 0) as avg_cost_per_analysis,
            COALESCE(MIN(api_cost_usd), 0) as min_cost,
            COALESCE(MAX(api_cost_usd), 0) as max_cost,
            SUM(tokens_used) as total_tokens,
            AVG(tokens_used) as avg_tokens_per_analysis
        FROM analyses;
    """

    cur.execute(query)
    row = cur.fetchone()

    print("\n" + "="*60)
    print("📊 ОБЩАЯ СТАТИСТИКА")
    print("="*60)
    print(f"Всего анализов: {row[0]}")
    print(f"Общая стоимость: ${row[1]:.4f}")
    print(f"Средняя стоимость: ${row[2]:.4f}")
    print(f"Мин/Макс стоимость: ${row[3]:.4f} / ${row[4]:.4f}")
    print(f"Всего токенов: {row[5]:,}")
    print(f"Средне токенов: {int(row[6]):,}")

    cur.close()
    conn.close()

def show_user_stats():
    """Статистика по пользователям"""
    conn = get_db()
    cur = conn.cursor()

    query = """
        SELECT
            u.username,
            u.first_name,
            COUNT(a.id) as analyses_count,
            COALESCE(SUM(a.api_cost_usd), 0) as total_spent_usd,
            COALESCE(AVG(a.api_cost_usd), 0) as avg_cost_per_analysis
        FROM users u
        JOIN analyses a ON u.user_id = a.user_id
        GROUP BY u.user_id, u.username, u.first_name
        ORDER BY total_spent_usd DESC
        LIMIT 10;
    """

    cur.execute(query)
    rows = cur.fetchall()

    print("\n" + "="*60)
    print("👥 ТОП-10 ПОЛЬЗОВАТЕЛЕЙ ПО РАСХОДАМ")
    print("="*60)

    table = []
    for row in rows:
        username = row[0] or "Нет username"
        name = row[1] or "Без имени"
        count = row[2]
        total = row[3]
        avg = row[4]
        table.append([username, name, count, f"${total:.4f}", f"${avg:.4f}"])

    headers = ["Username", "Имя", "Анализов", "Всего", "Средняя"]
    print(tabulate(table, headers=headers, tablefmt="grid"))

    cur.close()
    conn.close()

def show_recent_analyses():
    """Последние анализы с стоимостью"""
    conn = get_db()
    cur = conn.cursor()

    query = """
        SELECT
            a.id,
            u.username,
            LEFT(a.request_text, 40) as request_preview,
            COALESCE(a.api_cost_usd, 0) as cost,
            a.tokens_used,
            TO_CHAR(a.created_at, 'DD.MM.YYYY HH24:MI') as created
        FROM analyses a
        JOIN users u ON a.user_id = u.user_id
        ORDER BY a.created_at DESC
        LIMIT 10;
    """

    cur.execute(query)
    rows = cur.fetchall()

    print("\n" + "="*60)
    print("📝 ПОСЛЕДНИЕ 10 АНАЛИЗОВ")
    print("="*60)

    table = []
    for row in rows:
        table.append([
            row[0],  # ID
            row[1] or "Нет username",  # username
            row[2] + "...",  # request preview
            f"${row[3]:.4f}",  # cost
            f"{row[4]:,}",  # tokens
            row[5]  # date
        ])

    headers = ["ID", "User", "Запрос", "Стоимость", "Токены", "Дата"]
    print(tabulate(table, headers=headers, tablefmt="grid"))

    cur.close()
    conn.close()

if __name__ == "__main__":
    try:
        show_total_stats()
        show_user_stats()
        show_recent_analyses()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
