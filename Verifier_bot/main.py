import os
import re
import sqlite3
import logging
import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from telegram.error import BadRequest

from text import (
    START_TEXT,
    ALREADY_REGISTERED,
    STEP_PHONE,
    STEP_FIO,
    STEP_LOGIN,
    STEP_APIKEY,
    STEP_WORKGROUP_TEXT,
    STEP_PASSPORT_PHOTO_1,
    STEP_PASSPORT_PHOTO_2,
    STEP_VIDEO_REQUEST,
    FINISH_TEXT,
    INVALID_FORMAT,
)

from config import TOKEN, DATABASE_PATH, BASE_DIRECTORY

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

(
    WAIT_INLINE_BUTTON,
    STEP_COLLECT_PHONE,
    STEP_FIO_INPUT,
    STEP_LOGIN_INPUT,
    STEP_APIKEY_INPUT,
    STATE_WORKGROUP,
    STEP_PASS_PHOTO_1,
    STEP_PASS_PHOTO_2,
    STEP_VIDEO
) = range(1, 10)

def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_verification (
            user_id TEXT PRIMARY KEY,
            start_time TEXT,
            username TEXT,
            collect_fio TEXT,
            platform_login TEXT,
            api_key TEXT,
            workgroup_name TEXT,
            phone_number TEXT,
            passport_photo_1 TEXT,
            passport_photo_2 TEXT,
            video_file TEXT
        )
    ''')
    conn.commit()
    conn.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_dir = os.path.join(BASE_DIRECTORY, user_id)

    if os.path.exists(user_dir):
        await update.message.reply_text(ALREADY_REGISTERED, parse_mode="HTML")
        return ConversationHandler.END
    
    os.makedirs(user_dir, exist_ok=True)

    with open(os.path.join(user_dir, 'info.txt'), 'w', encoding='utf-8') as f:
        f.write(f"Start Time: {datetime.datetime.now()}\n")
        f.write(f"User ID: {user_id}\n")
        f.write(f"Username: {update.effective_user.username}\n")

    keyboard = [[InlineKeyboardButton("Начать", callback_data="start_verification")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(START_TEXT, reply_markup=reply_markup, parse_mode="HTML")
    return WAIT_INLINE_BUTTON

async def handle_inline_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [[KeyboardButton("Отправить контакт", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await query.message.reply_text(STEP_PHONE, parse_mode="HTML", reply_markup=reply_markup)
    return STEP_COLLECT_PHONE


async def step_collect_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_dir = os.path.join(BASE_DIRECTORY, user_id)

    if update.message.contact:
        phone = update.message.contact.phone_number
        logger.debug(f"ПОЛУЧЕН КОНТАКТ: {phone}")
    else:
        phone = update.message.text.strip()
        logger.debug(f"ПОЛУЧЕН ТЕКСТ: {phone}")

    with open(os.path.join(user_dir, 'info.txt'), 'a', encoding='utf-8') as f:
        f.write(f"phone_number: {phone}\n")

    await update.message.reply_text(
        STEP_FIO,
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )
    return STEP_FIO_INPUT

async def step_fio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_dir = os.path.join(BASE_DIRECTORY, user_id)

    fio = update.message.text.strip()
    logger.debug(f"ПОЛУЧЕНО ФИО: {fio}")

    with open(os.path.join(user_dir, 'info.txt'), 'a', encoding='utf-8') as f:
        f.write(f"collect_fio: {fio}\n")

    await update.message.reply_text(STEP_LOGIN, parse_mode="HTML")
    return STEP_LOGIN_INPUT

async def step_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_dir = os.path.join(BASE_DIRECTORY, user_id)

    login_txt = update.message.text.strip()
    logger.debug(f"ПОЛУЧЕН ЛОГИН: {login_txt}")

    with open(os.path.join(user_dir, 'info.txt'), 'a', encoding='utf-8') as f:
        f.write(f"platform_login: {login_txt}\n")

    await update.message.reply_text(STEP_APIKEY, parse_mode="HTML")
    return STEP_APIKEY_INPUT

async def step_apikey(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)
    user_dir = os.path.join(BASE_DIRECTORY, user_id)

    apikey_txt = update.message.text.strip()
    logger.debug(f"ПОЛУЧЕН API-KEY: {apikey_txt}")

    with open(os.path.join(user_dir, 'info.txt'), 'a', encoding='utf-8') as f:
        f.write(f"api_key: {apikey_txt}\n")

    await update.message.reply_text(STEP_WORKGROUP_TEXT, parse_mode="HTML")

    return STATE_WORKGROUP

async def step_workgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)
    user_dir = os.path.join(BASE_DIRECTORY, user_id)

    groupname = update.message.text.strip()
    logger.debug(f"ПОЛУЧЕНА WORKGROUP: {groupname}")

    with open(os.path.join(user_dir, 'info.txt'), 'a', encoding='utf-8') as f:
        f.write(f"workgroup_name: {groupname}\n")

    await update.message.reply_text(STEP_PASSPORT_PHOTO_1, parse_mode="HTML")
    return STEP_PASS_PHOTO_1

async def step_pass_photo_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo and not (
        update.message.document
        and update.message.document.mime_type
        and update.message.document.mime_type.startswith("image")
    ):
        await update.message.reply_text(INVALID_FORMAT, parse_mode="HTML")
        return STEP_PASS_PHOTO_1

    user_id = str(update.effective_user.id)
    user_dir = os.path.join(BASE_DIRECTORY, user_id)

    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        logger.debug(f"Фото1: {file_id}")
    else:
        file_id = update.message.document.file_id
        logger.debug(f"Фото1 (документ): {file_id}")

    file = await context.bot.get_file(file_id)
    local_path = os.path.join(user_dir, "passport_photo_1.jpg")
    await file.download_to_drive(local_path)

    await update.message.reply_text(STEP_PASSPORT_PHOTO_2, parse_mode="HTML")
    return STEP_PASS_PHOTO_2

async def step_pass_photo_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo and not (
        update.message.document
        and update.message.document.mime_type
        and update.message.document.mime_type.startswith("image")
    ):
        await update.message.reply_text(INVALID_FORMAT, parse_mode="HTML")
        return STEP_PASS_PHOTO_2

    user_id = str(update.effective_user.id)
    user_dir = os.path.join(BASE_DIRECTORY, user_id)

    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        logger.debug(f"Фото2: {file_id}")
    else:
        file_id = update.message.document.file_id
        logger.debug(f"Фото2 (документ): {file_id}")

    file = await context.bot.get_file(file_id)
    local_path = os.path.join(user_dir, "passport_photo_2.jpg")
    await file.download_to_drive(local_path)

    await update.message.reply_text(STEP_VIDEO_REQUEST, parse_mode="HTML")
    return STEP_VIDEO

async def step_video(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.video_note:
        user_id = str(update.effective_user.id)
        user_dir = os.path.join(BASE_DIRECTORY, user_id)
        file_id = update.message.video_note.file_id

        logger.debug(f"ВИДЕО (video_note): {file_id}")

        file = await context.bot.get_file(file_id)
        local_path = os.path.join(user_dir, "real_time_video.mp4")
        await file.download_to_drive(local_path)
        await update.message.reply_text(FINISH_TEXT, parse_mode="HTML")

        save_to_db(user_id)
        return ConversationHandler.END

    else:
        await update.message.reply_text(
            "Нужно отправить видеозаметку (кружок) в реальном времени.",
            parse_mode="HTML"
        )
        return STEP_VIDEO

def save_to_db(user_id: str):
    user_dir = os.path.join(BASE_DIRECTORY, user_id)
    info_file = os.path.join(user_dir, "info.txt")

    data = {
        "user_id": user_id,
        "start_time": "",
        "username": "",
        "collect_fio": "",
        "platform_login": "",
        "api_key": "",
        "workgroup_name": "",
        "phone_number": ""
    }

    if os.path.exists(info_file):
        with open(info_file, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()
        for line in lines:
            low_line = line.lower()
            if low_line.startswith("start time:"):
                data["start_time"] = line.split(":", 1)[1].strip()
            elif low_line.startswith("username:"):
                data["username"] = line.split(":", 1)[1].strip()
            elif low_line.startswith("phone_number:"):
                data["phone_number"] = line.split(":", 1)[1].strip()
            elif low_line.startswith("collect_fio:"):
                data["collect_fio"] = line.split(":", 1)[1].strip()
            elif low_line.startswith("platform_login:"):
                data["platform_login"] = line.split(":", 1)[1].strip()
            elif low_line.startswith("api_key:"):
                data["api_key"] = line.split(":", 1)[1].strip()
            elif low_line.startswith("workgroup_name:"):
                data["workgroup_name"] = line.split(":", 1)[1].strip()

    photo1_link = f"verifier_data/{user_id}/passport_photo_1.jpg"
    photo2_link = f"verifier_data/{user_id}/passport_photo_2.jpg"
    video_link  = f"verifier_data/{user_id}/real_time_video.mp4"

    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO user_verification (
            user_id, start_time, username, collect_fio, platform_login, api_key,
            workgroup_name, phone_number, passport_photo_1, passport_photo_2, video_file
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["user_id"],
        data["start_time"],
        data["username"],
        data["collect_fio"],
        data["platform_login"],
        data["api_key"],
        data["workgroup_name"],
        data["phone_number"],
        photo1_link,
        photo2_link,
        video_link
    ))
    conn.commit()
    conn.close()

def main():
    init_db()
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAIT_INLINE_BUTTON: [
                CallbackQueryHandler(handle_inline_button, pattern='^start_verification$')
            ],
            STEP_COLLECT_PHONE: [
                MessageHandler((filters.CONTACT | (filters.TEXT & ~filters.COMMAND)), step_collect_phone)
            ],
            STEP_FIO_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, step_fio)
            ],
            STEP_LOGIN_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, step_login)
            ],
            STEP_APIKEY_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, step_apikey)
            ],
            STATE_WORKGROUP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, step_workgroup)
            ],
            STEP_PASS_PHOTO_1: [
                MessageHandler(filters.ALL & ~filters.COMMAND, step_pass_photo_1)
            ],
            STEP_PASS_PHOTO_2: [
                MessageHandler(filters.ALL & ~filters.COMMAND, step_pass_photo_2)
            ],
            STEP_VIDEO: [
                MessageHandler(filters.ALL & ~filters.COMMAND, step_video)
            ],
        },
        fallbacks=[]
    )

    application.add_handler(conv_handler)

    logger.info("Запуск бота в режиме polling...")
    application.run_polling()

if __name__ == '__main__':
    main()
