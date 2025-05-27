import sqlite3
import os
from flask import render_template, send_from_directory, jsonify, make_response, send_file
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from io import BytesIO
import json
import zipfile
from datetime import datetime
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import config
import pytz

MOSCOW_TZ = pytz.timezone('Europe/Moscow')

font_path = os.path.join(config.TEMPLATE_DIR, 'LorenzoSans.ttf')
if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont('LorenzoSans', font_path))
else:
    raise FileNotFoundError(f"Шрифт LorenzoSans.ttf не найден в {config.TEMPLATE_DIR}")

def kyc():
    conn = sqlite3.connect(config.VERIFIER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, start_time, username, collect_fio,
               platform_login, api_key, workgroup_name, phone_number 
        FROM user_verification
    """)
    rows = cursor.fetchall()
    conn.close()

    data = []
    for i, row in enumerate(rows, start=1):
        user_id = row[0]
        user_path = os.path.join(config.BASE_DIRECTORY, user_id)
        photo1 = "passport_photo_1.jpg" if os.path.exists(os.path.join(user_path, "passport_photo_1.jpg")) else None
        photo2 = "passport_photo_2.jpg" if os.path.exists(os.path.join(user_path, "passport_photo_2.jpg")) else None
        video = "real_time_video.mp4" if os.path.exists(os.path.join(user_path, "real_time_video.mp4")) else None
        extended = (i,) + row + (photo1, photo2, video)
        data.append(extended)

    return render_template("kyc.html", data=data)

def serve_kyc_file(user_id, filename):
    directory = os.path.join(config.BASE_DIRECTORY, user_id)
    file_path = os.path.join(directory, filename)
    if not os.path.exists(file_path):
        return "Файл не найден", 404
    return send_from_directory(directory, filename)

def download_kyc_excel():
    conn = sqlite3.connect(config.VERIFIER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, start_time, username, collect_fio,
               platform_login, api_key, workgroup_name, phone_number
        FROM user_verification
    """)
    rows = cursor.fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Верификация by EXOTIC"

    headers = [
        '№', 'User ID', 'Время начала', 'Никнейм', 'ФИО',
        'Название рабочей группы', 'Гео работы', 'Адрес', 'Телефон'
    ]
    ws.append(headers)

    for i, row in enumerate(rows, start=1):
        formatted_time = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S.%f').strftime('%d.%m.%Y | %H:%M:%S') if row[1] else ""
        row_data = [i, row[0], formatted_time, row[2], row[3], row[4], row[5], row[6], row[7]]
        ws.append(row_data)

    mono_font = Font(name='Courier', size=10)
    center_alignment = Alignment(horizontal='center', vertical='center', wrap_text=False)

    for row in ws.iter_rows():
        for cell in row:
            cell.font = mono_font
            cell.alignment = center_alignment

    for col in ws.columns:
        max_length = max(len(str(cell.value or '')) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = max_length * 1.2

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="kyc_data.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def download_pdf_all():
    conn = sqlite3.connect(config.VERIFIER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, start_time, username, collect_fio,
               platform_login, api_key, workgroup_name, phone_number
        FROM user_verification
    """)
    rows = cursor.fetchall()
    conn.close()

    pdf_path = os.path.join(config.BASE_DIRECTORY, "kyc_all_users.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, topMargin=25*mm, bottomMargin=25*mm, leftMargin=20*mm, rightMargin=20*mm)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', fontName='LorenzoSans', fontSize=24, textColor=colors.HexColor('#2b6cb0'), alignment=1, spaceAfter=30, bold=False)
    header_style = ParagraphStyle('Header', fontName='LorenzoSans', fontSize=14, textColor=colors.HexColor('#4a5568'), spaceAfter=6, bold=False)
    value_style = ParagraphStyle('Value', fontName='LorenzoSans', fontSize=12, textColor=colors.HexColor('#1a202c'), spaceAfter=6, bold=False)
    footer_style = ParagraphStyle('Footer', fontName='LorenzoSans', fontSize=10, textColor=colors.HexColor('#4a5568'), alignment=1, bold=False)
    page_num_style = ParagraphStyle('PageNum', fontName='LorenzoSans', fontSize=10, textColor=colors.HexColor('#4a5568'), alignment=1, bold=False)

    for i, row in enumerate(rows, 1):
        user_data = {
            "User ID": row[0],
            "Время": datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S.%f').strftime('%d.%m.%Y | %H:%M:%S') if row[1] else "",
            "Никнейм": row[2],
            "ФИО": row[3],
            "Название рабочей группы": row[4],
            "Гео работы": row[5],
            "Адрес": row[6],
            "Телефон": row[7]
        }
        user_path = os.path.join(config.BASE_DIRECTORY, row[0])
        photo1_path = os.path.join(user_path, "passport_photo_1.jpg") if os.path.exists(os.path.join(user_path, "passport_photo_1.jpg")) else None
        photo2_path = os.path.join(user_path, "passport_photo_2.jpg") if os.path.exists(os.path.join(user_path, "passport_photo_2.jpg")) else None

        elements.append(Paragraph(user_data["ФИО"], title_style))
        table_data = [[Paragraph(key, header_style), Paragraph(value or "-", value_style)] for key, value in user_data.items()]
        table = Table(table_data, colWidths=[90*mm, 80*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ffffff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a202c')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'LorenzoSans'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROUNDEDCORNERS', (0, 0), (-1, -1), [12, 12, 12, 12]),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f7fafc')])
        ]))
        elements.append(table)
        elements.append(Spacer(1, 30*mm))

        if photo1_path or photo2_path:
            images = []
            max_width = 85*mm
            max_height = 65*mm
            if photo1_path:
                img = PILImage.open(photo1_path)
                width, height = img.size
                aspect = width / height
                if width > max_width or height > max_height:
                    if aspect > 1:
                        draw_width = max_width
                        draw_height = max_width / aspect
                    else:
                        draw_height = max_height
                        draw_width = max_height * aspect
                else:
                    draw_width = width * 0.264583
                    draw_height = height * 0.264583
                img1 = Image(photo1_path, width=draw_width, height=draw_height)
                images.append(img1)
            if photo2_path:
                img = PILImage.open(photo2_path)
                width, height = img.size
                aspect = width / height
                if width > max_width or height > max_height:
                    if aspect > 1:
                        draw_width = max_width
                        draw_height = max_width / aspect
                    else:
                        draw_height = max_height
                        draw_width = max_height * aspect
                else:
                    draw_width = width * 0.264583
                    draw_height = height * 0.264583
                img2 = Image(photo2_path, width=draw_width, height=draw_height)
                images.append(img2)
            photo_table = Table([images], colWidths=[max_width + 5*mm] * len(images))
            photo_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('ROUNDEDCORNERS', (0, 0), (-1, -1), [12, 12, 12, 12]),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ffffff')),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5)
            ]))
            elements.append(photo_table)
        if i < len(rows):
            elements.append(PageBreak())

    def add_page_decorations(canvas, doc):
        canvas.saveState()
        page_num = canvas.getPageNumber()
        if page_num > 0:
            page_text = f"Страница {page_num}"
            p = Paragraph(page_text, page_num_style)
            w, h = p.wrap(doc.width, doc.topMargin)
            p.drawOn(canvas, (A4[0] - w) / 2, A4[1] - 15*mm)
        footer_text = f"Сгенерировано {datetime.now(MOSCOW_TZ).strftime('%d.%m.%Y | %H:%M:%S')} by <color rgb='#2b6cb0'>/EXOTIC</color>"
        p = Paragraph(footer_text, footer_style)
        w, h = p.wrap(doc.width, doc.bottomMargin)
        p.drawOn(canvas, (A4[0] - w) / 2, 10*mm)
        canvas.restoreState()

    doc.build(elements, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)

    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True, download_name="kyc_all_users.pdf")
    return "Ошибка: PDF-файл не был создан", 500

def download_user_pdf(user_id):
    conn = sqlite3.connect(config.VERIFIER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, start_time, username, collect_fio,
               platform_login, api_key, workgroup_name, phone_number
        FROM user_verification WHERE user_id = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return "Пользователь не найден", 404

    user_data = {
        "User ID": row[0],
        "Время": datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S.%f').strftime('%d.%m.%Y | %H:%M:%S') if row[1] else "",
        "Никнейм": row[2],
        "ФИО": row[3],
        "Название рабочей группы": row[4],
        "Гео работы": row[5],
        "Адрес": row[6],
        "Телефон": row[7]
    }

    user_path = os.path.join(config.BASE_DIRECTORY, user_id)
    photo1_path = os.path.join(user_path, "passport_photo_1.jpg") if os.path.exists(os.path.join(user_path, "passport_photo_1.jpg")) else None
    photo2_path = os.path.join(user_path, "passport_photo_2.jpg") if os.path.exists(os.path.join(user_path, "passport_photo_2.jpg")) else None

    pdf_path = os.path.join(config.BASE_DIRECTORY, f"kyc_{user_id}.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, topMargin=25*mm, bottomMargin=25*mm, leftMargin=20*mm, rightMargin=20*mm)
    elements = []

    styles = getSampleStyleSheet()
    header_style = ParagraphStyle('Header', fontName='LorenzoSans', fontSize=28, textColor=colors.HexColor('#2b6cb0'), alignment=1, spaceAfter=20, bold=False)
    title_style = ParagraphStyle('Title', fontName='LorenzoSans', fontSize=24, textColor=colors.HexColor('#2b6cb0'), alignment=1, spaceAfter=30, bold=False)
    field_header_style = ParagraphStyle('FieldHeader', fontName='LorenzoSans', fontSize=14, textColor=colors.HexColor('#4a5568'), spaceAfter=6, bold=False)
    value_style = ParagraphStyle('Value', fontName='LorenzoSans', fontSize=12, textColor=colors.HexColor('#1a202c'), spaceAfter=6, bold=False)
    footer_style = ParagraphStyle('Footer', fontName='LorenzoSans', fontSize=10, textColor=colors.HexColor('#4a5568'), alignment=1, bold=False)

    elements.append(Paragraph("EXOTIC", header_style))
    elements.append(Paragraph(user_data["ФИО"], title_style))

    table_data = [[Paragraph(key, field_header_style), Paragraph(value or "-", value_style)] for key, value in user_data.items()]
    table = Table(table_data, colWidths=[90*mm, 80*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ffffff')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a202c')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'LorenzoSans'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROUNDEDCORNERS', (0, 0), (-1, -1), [12, 12, 12, 12]),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f7fafc')])
    ]))
    elements.append(table)
    elements.append(Spacer(1, 30*mm))

    if photo1_path or photo2_path:
        images = []
        max_width = 85*mm
        max_height = 65*mm
        if photo1_path:
            img = PILImage.open(photo1_path)
            width, height = img.size
            aspect = width / height
            if width > max_width or height > max_height:
                if aspect > 1:
                    draw_width = max_width
                    draw_height = max_width / aspect
                else:
                    draw_height = max_height
                    draw_width = max_height * aspect
            else:
                draw_width = width * 0.264583
                draw_height = height * 0.264583
            img1 = Image(photo1_path, width=draw_width, height=draw_height)
            images.append(img1)
        if photo2_path:
            img = PILImage.open(photo2_path)
            width, height = img.size
            aspect = width / height
            if width > max_width or height > max_height:
                if aspect > 1:
                    draw_width = max_width
                    draw_height = max_width / aspect
                else:
                    draw_height = max_height
                    draw_width = max_height * aspect
            else:
                draw_width = width * 0.264583
                draw_height = height * 0.264583
            img2 = Image(photo2_path, width=draw_width, height=draw_height)
            images.append(img2)
        photo_table = Table([images], colWidths=[max_width + 5*mm] * len(images))
        photo_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROUNDEDCORNERS', (0, 0), (-1, -1), [12, 12, 12, 12]),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ffffff')),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5)
        ]))
        elements.append(photo_table)

    def add_page_decorations(canvas, doc):
        canvas.saveState()
        footer_text = f"Сгенерировано {datetime.now(MOSCOW_TZ).strftime('%d.%m.%Y | %H:%M:%S')} by <color rgb='#2b6cb0'>EXOTIC</color>"
        p = Paragraph(footer_text, footer_style)
        w, h = p.wrap(doc.width, doc.bottomMargin)
        p.drawOn(canvas, (A4[0] - w) / 2, 10*mm)
        canvas.restoreState()

    doc.build(elements, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)

    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True, download_name=f"kyc_{user_data['ФИО']}.pdf")
    return "Ошибка: PDF-файл не был создан", 500

def download_kyc_json():
    conn = sqlite3.connect(config.VERIFIER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, start_time, username, collect_fio,
               platform_login, api_key, workgroup_name, phone_number
        FROM user_verification
    """)
    rows = cursor.fetchall()
    conn.close()

    users = []
    for row in rows:
        user = {
            'user_id': row[0],
            'start_time': row[1],
            'username': row[2],
            'collect_fio': row[3],
            'platform_login': row[4],
            'api_key': row[5],
            'workgroup_name': row[6],
            'phone_number': row[7]
        }
        users.append(user)

    json_data = json.dumps(users, ensure_ascii=False, indent=4)
    response = make_response(json_data)
    response.headers['Content-Disposition'] = 'attachment; filename=kyc_data.json'
    response.headers['Content-Type'] = 'application/json'
    return response

def download_kyc_all_zips():
    conn = sqlite3.connect(config.VERIFIER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, collect_fio FROM user_verification")
    rows = cursor.fetchall()
    conn.close()

    memory_zip = BytesIO()
    with zipfile.ZipFile(memory_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for row in rows:
            user_id = row[0]
            fio = row[1].replace(' ', '_') if row[1] else user_id
            user_dir = os.path.join(config.BASE_DIRECTORY, user_id)
            pdf_path = os.path.join(config.BASE_DIRECTORY, f"kyc_{user_id}.pdf")

            download_user_pdf(user_id)
            if os.path.exists(pdf_path):
                zf.write(pdf_path, os.path.join(fio, f"kyc_{fio}.pdf"))
                os.remove(pdf_path)

            if os.path.exists(user_dir):
                for root, _, files in os.walk(user_dir):
                    for file in files:
                        if file.endswith(('.jpg', '.mp4')):
                            file_path = os.path.join(root, file)
                            arcname = os.path.join(fio, file)
                            zf.write(file_path, arcname)

    memory_zip.seek(0)
    return send_file(
        memory_zip,
        as_attachment=True,
        download_name='kyc_selected_users.zip',
        mimetype='application/zip'
    )