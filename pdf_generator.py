"""
Модуль для генерации красивых PDF отчетов
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Image
)
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import re


def replace_emoji_for_pdf(text):
    """Замена эмодзи на текстовые символы для корректного отображения в PDF"""
    emoji_map = {
        '🔴': '[1]',  # Красная чакра
        '🟠': '[2]',  # Оранжевая чакра
        '🟡': '[3]',  # Жёлтая чакра
        '💚': '[4]',  # Зелёная чакра
        '💙': '[5]',  # Голубая чакра
        '💜': '[6]',  # Фиолетовая чакра
        '🤍': '[7]',  # Белая чакра
        '✨': '*',
        '🔮': '~',
        '🌿': '~',
        '💫': '*',
        '🕊': '~',
        '🌸': '~',
        '🔹': '•',
    }

    for emoji, replacement in emoji_map.items():
        text = text.replace(emoji, replacement)

    return text


def register_fonts():
    """Регистрация шрифтов с кириллицей"""
    try:
        # Пробуем использовать системные шрифты macOS
        pdfmetrics.registerFont(TTFont('DejaVuSans', '/System/Library/Fonts/Supplemental/DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/System/Library/Fonts/Supplemental/DejaVuSans-Bold.ttf'))
        return True
    except:
        try:
            # Альтернативный вариант для Linux
            pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
            return True
        except:
            # Если не получилось, используем стандартные шрифты
            return False


def create_custom_styles(has_custom_fonts=False):
    """Создание кастомных стилей для документа"""
    styles = getSampleStyleSheet()

    font_name = 'DejaVuSans' if has_custom_fonts else 'Helvetica'
    font_name_bold = 'DejaVuSans-Bold' if has_custom_fonts else 'Helvetica-Bold'

    # Стиль заголовка
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontName=font_name_bold,
        fontSize=18,
        textColor=colors.HexColor('#4A148C'),
        spaceAfter=30,
        alignment=TA_CENTER,
        leading=22
    ))

    # Стиль подзаголовка
    styles.add(ParagraphStyle(
        name='CustomHeading',
        parent=styles['Heading2'],
        fontName=font_name_bold,
        fontSize=14,
        textColor=colors.HexColor('#6A1B9A'),
        spaceAfter=12,
        spaceBefore=16,
        leading=18
    ))

    # Стиль основного текста
    styles.add(ParagraphStyle(
        name='CustomBody',
        parent=styles['BodyText'],
        fontName=font_name,
        fontSize=11,
        textColor=colors.HexColor('#212121'),
        alignment=TA_JUSTIFY,
        spaceAfter=10,
        leading=16
    ))

    # Стиль для трансформационных фраз
    styles.add(ParagraphStyle(
        name='TransformPhrase',
        parent=styles['BodyText'],
        fontName=font_name,
        fontSize=11,
        textColor=colors.HexColor('#1565C0'),
        alignment=TA_LEFT,
        spaceAfter=8,
        spaceBefore=8,
        leftIndent=20,
        leading=16,
        backColor=colors.HexColor('#E3F2FD')
    ))

    # Стиль для запроса
    styles.add(ParagraphStyle(
        name='RequestStyle',
        parent=styles['BodyText'],
        fontName=font_name,
        fontSize=12,
        textColor=colors.HexColor('#C62828'),
        alignment=TA_CENTER,
        spaceAfter=20,
        spaceBefore=10,
        leading=16
    ))

    return styles


def parse_analysis_sections(text):
    """Парсинг текста анализа на секции"""
    sections = {}

    # Паттерны для поиска секций (поддержка обоих форматов: точка и скобка)
    patterns = {
        'title': r'Сканер подсознания.*?для\s+(\w+)',
        'request': r'\*\*Запрос:\*\*\s*\n(.*?)(?=\n\*\*|$)',
        'contracts': r'\*\*1[\.\)]\s*Контракты и подключки\*\*\s*\n(.*?)(?=\n\*\*|$)',
        'layers': r'\*\*2[\.\)]\s*Слои.*?\*\*\s*\n(.*?)(?=\n\*\*|$)',
        'energy': r'\*\*3[\.\)]\s*Поток энергии по центрам\*\*\s*\n(.*?)(?=\n\*\*|$)',
        'programs': r'\*\*4[\.\)]\s*Главные программы.*?\*\*\s*\n(.*?)(?=\n\*\*|$)',
        'lessons': r'\*\*5[\.\)]\s*Главные уроки души\*\*\s*\n(.*?)(?=\n\*\*|$)',
        'family': r'\*\*6[\.\)]\s*Родовые влияния\*\*\s*\n(.*?)(?=\n\*\*|$)',
        'past_lives': r'\*\*7[\.\)]\s*Связи из прошлых жизней\*\*\s*\n(.*?)(?=\n\*\*|$)',
        'changes': r'\*\*8[\.\)]\s*Что важно изменить\*\*\s*\n(.*?)(?=\n\*\*|$)',
        'phrases': r'\*\*9[\.\)]\s*Трансформационные фразы\*\*\s*\n(.*?)(?=\n\*\*|\n💫|$)',
        'recommendation': r'\*\*10[\.\)]\s*Рекомендация: следующий шаг\*\*\s*\n(.*?)(?=\n\*\*|$)',
        'archetype': r'\*\*11[\.\)]\s*Архетипический анализ.*?\*\*\s*🕊?\s*\n(.*?)(?=\n💫|\n\*\*|$)',
        'message': r'💫\s*\*\*Вдохновляющее послание\*\*\s*\n(.*?)$',
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            if key == 'title':
                sections[key] = match.group(1)
            else:
                sections[key] = match.group(1).strip()

    return sections


def create_analysis_pdf(analysis_text, username, request_text):
    """
    Создание PDF документа с результатами анализа

    Args:
        analysis_text: Текст анализа от GPT
        username: Имя пользователя
        request_text: Запрос пользователя

    Returns:
        str: Путь к созданному PDF файлу
    """
    # Создаём папку для PDF
    os.makedirs('generated_pdfs', exist_ok=True)

    # Путь к файлу
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f'generated_pdfs/scanner_{username}_{timestamp}.pdf'

    # Регистрация шрифтов
    has_custom_fonts = register_fonts()

    # Создание документа
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    # Получение стилей
    styles = create_custom_styles(has_custom_fonts)

    # Контейнер для элементов
    story = []

    # Заменяем эмодзи на текстовые символы для PDF
    analysis_text_clean = replace_emoji_for_pdf(analysis_text)

    # Парсим анализ
    sections = parse_analysis_sections(analysis_text_clean)

    # Заголовок
    title = Paragraph(
        f"Сканер подсознания по Мета-Методу<br/>для {username}",
        styles['CustomTitle']
    )
    story.append(title)
    story.append(Spacer(1, 0.5*cm))

    # Дата
    date_text = Paragraph(
        f"<i>Дата анализа: {datetime.now().strftime('%d.%m.%Y')}</i>",
        styles['CustomBody']
    )
    story.append(date_text)
    story.append(Spacer(1, 0.8*cm))

    # Запрос
    request_header = Paragraph("Запрос:", styles['CustomHeading'])
    story.append(request_header)
    request_para = Paragraph(
        f"<i>{request_text}</i>",
        styles['RequestStyle']
    )
    story.append(request_para)
    story.append(Spacer(1, 0.5*cm))

    # Основные секции
    section_titles = {
        'contracts': '1. Контракты и подключки',
        'layers': '2. Слои',
        'energy': '3. Поток энергии по центрам',
        'programs': '4. Главные программы',
        'lessons': '5. Главные уроки души',
        'family': '6. Родовые влияния',
        'past_lives': '7. Связи из прошлых жизней',
        'changes': '8. Что важно изменить',
        'phrases': '9. Трансформационные фразы',
        'recommendation': '10. Рекомендация: следующий шаг',
        'archetype': '11. Архетипический анализ 🕊',
        'message': '💫 Вдохновляющее послание',
    }

    for key, title in section_titles.items():
        if key in sections and sections[key]:
            # Заголовок секции
            section_title = Paragraph(title, styles['CustomHeading'])
            story.append(section_title)

            # Контент секции
            content = sections[key]

            # Особая обработка для трансформационных фраз
            if key == 'phrases':
                # Разбиваем на отдельные фразы
                phrases = content.split('\n')
                for phrase in phrases:
                    if phrase.strip():
                        phrase_para = Paragraph(phrase.strip(), styles['TransformPhrase'])
                        story.append(phrase_para)

            # Особая обработка для чакр (каждая с новой строки)
            elif key == 'energy':
                # Разбиваем по эмодзи чакр или по строкам
                lines = content.split('\n')
                current_para = []

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # Если строка начинается с эмодзи чакры или маркера
                    if any(emoji in line[:5] for emoji in ['🔴', '🟠', '🟡', '💚', '💙', '💜', '🤍', '-', '•', 'Чакра']):
                        # Если накопились предыдущие строки, создаем параграф
                        if current_para:
                            para = Paragraph('<br/>'.join(current_para), styles['CustomBody'])
                            story.append(para)
                            current_para = []
                        # Добавляем текущую строку
                        current_para.append(line)
                    else:
                        # Продолжение предыдущей строки
                        if current_para:
                            current_para[-1] += ' ' + line
                        else:
                            current_para.append(line)

                # Добавляем оставшееся
                if current_para:
                    para = Paragraph('<br/>'.join(current_para), styles['CustomBody'])
                    story.append(para)

            # Особая обработка для списков программ, изменений
            elif key in ['programs', 'changes']:
                # Разбиваем по строкам с маркерами
                lines = content.split('\n')
                items = []

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # Если строка начинается с маркера или кавычки
                    if line.startswith(('-', '•', '"', '–', '—')):
                        items.append(line)
                    elif items:
                        # Продолжение предыдущего пункта
                        items[-1] += ' ' + line
                    else:
                        items.append(line)

                if items:
                    para = Paragraph('<br/>'.join(items), styles['CustomBody'])
                    story.append(para)

            else:
                # Обычный текст - разбиваем по двойным переносам
                paragraphs = content.split('\n\n')
                for para_text in paragraphs:
                    para_text = para_text.strip()
                    if para_text:
                        # Заменяем одинарные переносы на пробелы внутри параграфа
                        para_text = para_text.replace('\n', ' ')
                        para = Paragraph(para_text, styles['CustomBody'])
                        story.append(para)

            story.append(Spacer(1, 0.3*cm))

    # Футер
    story.append(Spacer(1, 1*cm))
    footer_line = Paragraph(
        "<i>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</i>",
        styles['CustomBody']
    )
    story.append(footer_line)

    footer_text = Paragraph(
        "<i>Работай с трансформационными фразами каждый день.<br/>"
        "Проговаривай их вслух или про себя, чувствуя каждое слово.<br/>"
        "Изменения придут через действие и осознанность. 🙏</i>",
        styles['CustomBody']
    )
    story.append(footer_text)

    # Генерация PDF
    doc.build(story)

    return pdf_filename


# Тестовая функция
if __name__ == '__main__':
    test_analysis = """
**Сканер подсознания по Мета-Методу для Тестовый**

**Запрос:**
Тестовый запрос для проверки генерации PDF

**1) Контракты и подключки**
Есть активный контракт на самообесценивание.

**9) Трансформационные фразы**
Я признаю и даю место всем опытам в этой жизни.
Я люблю нас так, как Бог нас любит.
Открываюсь новому и даю место новому.

**10) Рекомендация: следующий шаг**
Работать с установкой каждый день.
"""

    pdf_path = create_analysis_pdf(test_analysis, "Тест", "Тестовый запрос")
    print(f"PDF создан: {pdf_path}")
