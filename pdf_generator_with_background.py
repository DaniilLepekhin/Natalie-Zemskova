"""
Модуль для генерации красивых PDF отчетов с фоновым изображением
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import re


def replace_emoji_for_pdf(text):
    """Замена эмодзи на текстовые символы для корректного отображения в PDF"""
    emoji_map = {
        '🔴': '[1]',
        '🟠': '[2]',
        '🟡': '[3]',
        '💚': '[4]',
        '💙': '[5]',
        '💜': '[6]',
        '🤍': '[7]',
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
        # Для Linux сервера
        pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
        return True
    except:
        return False


def add_background(canvas, doc, background_path):
    """Функция для добавления фона на каждую страницу"""
    if background_path and os.path.exists(background_path):
        canvas.saveState()
        page_width, page_height = A4
        canvas.drawImage(
            background_path,
            0, 0,
            width=page_width,
            height=page_height,
            preserveAspectRatio=False
        )
        canvas.restoreState()


def create_custom_styles(has_custom_fonts=False):
    """Создание кастомных стилей для документа"""
    styles = getSampleStyleSheet()

    font_name = 'DejaVuSans' if has_custom_fonts else 'Helvetica'
    font_name_bold = 'DejaVuSans-Bold' if has_custom_fonts else 'Helvetica-Bold'

    # Темные контрастные цвета для хорошей читаемости
    title_color = colors.HexColor('#8B4F62')  # Темно-розовый для заголовков
    heading_color = colors.HexColor('#6B3D4F')  # Еще темнее для подзаголовков
    body_color = colors.HexColor('#2D2327')  # Почти черный для текста

    # Стиль заголовка
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontName=font_name_bold,
        fontSize=20,
        textColor=title_color,
        spaceAfter=20,
        spaceBefore=40,
        alignment=TA_CENTER,
        leading=24
    ))

    # Стиль подзаголовка
    styles.add(ParagraphStyle(
        name='CustomHeading',
        parent=styles['Heading2'],
        fontName=font_name_bold,
        fontSize=13,
        textColor=heading_color,
        spaceAfter=10,
        spaceBefore=14,
        leading=16,
        keepWithNext=True
    ))

    # Стиль основного текста
    styles.add(ParagraphStyle(
        name='CustomBody',
        parent=styles['BodyText'],
        fontName=font_name,
        fontSize=10,
        textColor=body_color,
        spaceAfter=8,
        leading=14,
        alignment=TA_LEFT
    ))

    # Стиль запроса
    styles.add(ParagraphStyle(
        name='RequestStyle',
        parent=styles['BodyText'],
        fontName=font_name,
        fontSize=11,
        textColor=colors.HexColor('#6B3D4F'),
        spaceAfter=16,
        spaceBefore=10,
        leading=15,
        alignment=TA_CENTER
    ))

    return styles


def generate_pdf(analysis_text, username, output_path='analysis.pdf', background_path='pdf_background.png'):
    """
    Генерирует красивый PDF отчет с фоновым изображением

    Args:
        analysis_text: текст анализа
        username: имя пользователя
        output_path: путь для сохранения PDF
        background_path: путь к фоновому изображению
    """

    # Регистрируем шрифты
    has_fonts = register_fonts()

    # Заменяем эмодзи на текстовые символы
    analysis_text = replace_emoji_for_pdf(analysis_text)

    # Создаем PDF с функцией для добавления фона
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=6*cm,
        bottomMargin=3*cm
    )

    # Получаем стили
    styles = create_custom_styles(has_fonts)

    # Список элементов документа
    story = []

    # Парсим текст анализа
    lines = analysis_text.strip().split('\n')

    for line in lines:
        line = line.strip()

        if not line:
            story.append(Spacer(1, 0.3*cm))
            continue

        # Пропускаем заголовок "Сканер подсознания" - он уже на фоне
        if 'Сканер подсознания' in line or '✨' in line:
            continue  # Пропускаем эту строку

        # Запрос
        elif line.startswith("🔹") and "Запрос:" in line:
            clean_line = line.replace("🔹", "").strip()
            story.append(Paragraph(clean_line, styles["CustomHeading"]))
            continue
        # Подзаголовки разделов (с номерами)
        elif re.match(r'^\*?\*?\d+\.', line) or line.startswith('**'):
            clean_line = line.replace('**', '').strip()
            story.append(Paragraph(clean_line, styles['CustomHeading']))
            
            # Разрыв страницы после 4-го раздела
            if clean_line.startswith('5.'):
                story.append(PageBreak())

        # Обычный текст
        else:
            # Обрабатываем списки
            if line.startswith('—') or line.startswith('-') or line.startswith('•'):
                clean_line = '  ' + line
            else:
                clean_line = line

            story.append(Paragraph(clean_line, styles['CustomBody']))

    # Добавляем футер с датой
    story.append(Spacer(1, 1*cm))
    footer_text = f"<font size=8 color='#6B3D4F'>Сгенерировано {datetime.now().strftime('%d.%m.%Y')}</font>"
    footer = Paragraph(footer_text, styles['CustomBody'])
    story.append(footer)

    # Создаем PDF с фоном на каждой странице
    doc.build(
        story,
        onFirstPage=lambda c, d: add_background(c, d, background_path),
        onLaterPages=lambda c, d: add_background(c, d, background_path)
    )

    return output_path
