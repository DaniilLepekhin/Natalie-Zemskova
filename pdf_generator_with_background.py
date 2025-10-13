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
from reportlab.pdfgen import canvas
from PIL import Image
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
        # Для macOS
        pdfmetrics.registerFont(TTFont('DejaVuSans', '/System/Library/Fonts/Supplemental/DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/System/Library/Fonts/Supplemental/DejaVuSans-Bold.ttf'))
        print("✅ Шрифты DejaVu загружены (macOS)")
        return True
    except Exception as e1:
        try:
            # Для Linux сервера
            pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
            print("✅ Шрифты DejaVu загружены (Linux)")
            return True
        except Exception as e2:
            print(f"⚠️ Не удалось загрузить DejaVu: {e1}, {e2}")
            print("ℹ️ Используем стандартные шрифты (без кириллицы)")
            return False


class BackgroundCanvas(canvas.Canvas):
    """Кастомный Canvas с фоновым изображением"""

    def __init__(self, *args, **kwargs):
        self.background_path = kwargs.pop('background_path', None)
        canvas.Canvas.__init__(self, *args, **kwargs)

    def showPage(self):
        """Добавляем фон перед отрисовкой страницы"""
        if self.background_path and os.path.exists(self.background_path):
            # Получаем размеры страницы A4
            page_width, page_height = A4

            # Рисуем фон на всю страницу
            self.drawImage(
                self.background_path,
                0, 0,
                width=page_width,
                height=page_height,
                preserveAspectRatio=False,
                mask='auto'
            )

        canvas.Canvas.showPage(self)


def create_custom_styles(has_custom_fonts=False):
    """Создание кастомных стилей для документа"""
    styles = getSampleStyleSheet()

    font_name = 'DejaVuSans' if has_custom_fonts else 'Helvetica'
    font_name_bold = 'DejaVuSans-Bold' if has_custom_fonts else 'Helvetica-Bold'

    # Цвета в стиле дизайна (розовые оттенки)
    title_color = colors.HexColor('#C97A8F')  # Розовый из дизайна
    heading_color = colors.HexColor('#B06A7F')  # Темно-розовый
    body_color = colors.HexColor('#5A4A4E')  # Темно-серый для текста

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
        leading=16
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
        textColor=colors.HexColor('#8A6A6F'),
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

    # Создаем PDF с кастомным Canvas
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2.5*cm,
        bottomMargin=2*cm
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

        # Заголовок "Сканер подсознания"
        if 'Сканер подсознания' in line or '✨' in line:
            story.append(Paragraph(line, styles['CustomTitle']))

        # Запрос
        elif line.startswith('🔹') and 'Запрос:' in line:
            clean_line = line.replace('🔹', '').replace('Запрос:', '<b>Запрос:</b>').strip()
            story.append(Paragraph(clean_line, styles['RequestStyle']))

        # Подзаголовки разделов (с номерами)
        elif re.match(r'^\*?\*?\d+\.', line) or line.startswith('**'):
            clean_line = line.replace('**', '').strip()
            story.append(Paragraph(clean_line, styles['CustomHeading']))

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
    footer_text = f"<font size=8 color='#A08A8E'>Сгенерировано {datetime.now().strftime('%d.%m.%Y')}</font>"
    footer = Paragraph(footer_text, styles['CustomBody'])
    story.append(footer)

    # Создаем PDF с фоном
    doc.build(
        story,
        canvasmaker=lambda *args, **kwargs: BackgroundCanvas(
            *args,
            background_path=background_path if os.path.exists(background_path) else None,
            **kwargs
        )
    )

    return output_path


# Для тестирования
if __name__ == '__main__':
    test_text = """
✨ **Сканер подсознания по Мета-Методу для Тестового Пользователя**

🔹 **Запрос:**
"Что мне мешает встретить свою вторую половину?"

**1. Контракты и подключки**
Контракт: «Я никогда не найду свою настоящую любовь». Это ограничение глубоко укоренилось в вашем подсознании.

**2. Слои (откуда идёт программа)**
Программа тянется из глубин рода. Любовь часто скрывалась за маской долга. Семейные ветви обременены страхом быть отвергнутыми.

**3. Поток энергии по центрам**
— Муладхара ослаблена, ощущение нестабильности
— Свадхистхана сжата — чувства блокируются
— Манипура перекрыта, уверенность тает

**10. Рекомендация: следующий шаг**
Начать практику «маленьких радостей»: каждый день находите одну вещь для удовольствия.
"""

    generate_pdf(test_text, "Тест", "test_output.pdf")
    print("✅ Тестовый PDF создан!")
