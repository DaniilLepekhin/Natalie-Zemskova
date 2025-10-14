"""
Модуль для расчёта стоимости API запросов к OpenAI
"""

# Цены GPT-4o (на декабрь 2024)
# https://openai.com/api/pricing/
GPT4O_PRICES = {
    'gpt-4o': {
        'prompt': 0.0025,      # $2.50 за 1M токенов = $0.0025 за 1K
        'completion': 0.010    # $10.00 за 1M токенов = $0.010 за 1K
    },
    'gpt-4o-mini': {
        'prompt': 0.00015,     # $0.15 за 1M токенов
        'completion': 0.0006   # $0.60 за 1M токенов
    }
}

def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Рассчитывает стоимость запроса в USD
    
    Args:
        model: название модели (gpt-4o, gpt-4o-mini)
        prompt_tokens: количество токенов в промпте
        completion_tokens: количество токенов в ответе
        
    Returns:
        float: стоимость в долларах США
    """
    if model not in GPT4O_PRICES:
        # Если модель неизвестна, используем цены gpt-4o
        model = 'gpt-4o'
    
    prices = GPT4O_PRICES[model]
    
    # Переводим токены в тысячи и умножаем на цену
    prompt_cost = (prompt_tokens / 1000) * prices['prompt']
    completion_cost = (completion_tokens / 1000) * prices['completion']
    
    total_cost = prompt_cost + completion_cost
    
    return round(total_cost, 6)  # Округляем до 6 знаков после запятой


def format_cost(cost_usd: float) -> str:
    """
    Форматирует стоимость для отображения
    
    Args:
        cost_usd: стоимость в долларах
        
    Returns:
        str: отформатированная строка, например "$0.0234"
    """
    return f"${cost_usd:.4f}"
