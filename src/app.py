import os
import io
import json
import zipfile
import logging
import sqlite3
import threading
import pytz
import requests
import sys
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, send_from_directory, send_file, jsonify
)
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.drawing.image import Image
from matplotlib.backends.backend_pdf import PdfPages
import config
from backend.kyc import kyc, serve_kyc_file, download_kyc_excel, download_pdf_all, download_user_pdf, download_kyc_json, download_kyc_all_zips
from flask_cors import CORS

app = Flask(__name__, template_folder=config.TEMPLATE_DIR, static_folder=config.STATIC_DIR)
CORS(app)
app.secret_key = config.SECRET_KEY
app.permanent_session_lifetime = timedelta(hours=6)

UPLOAD_FOLDER = os.path.join(config.STATIC_DIR, 'files')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

log_buffer = []
class BufferLogHandler(logging.Handler):
    def emit(self, record):
        log_message = self.format(record)
        log_buffer.append(log_message)
        if len(log_buffer) > 10000:
            log_buffer.pop(0)

buffer_handler = BufferLogHandler()
buffer_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(buffer_handler)
logging.getLogger().setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

matplotlib_lock = threading.Lock()
MOSCOW_TZ = pytz.timezone('Europe/Moscow')

def login_required(f):
    def wrapper(*args, **kwargs):
        if 'logged_in' not in session:
            session['next'] = request.url
            return redirect(url_for('login'))
        session.modified = True
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/', methods=['GET'])
def index():
    if 'logged_in' in session:
        return redirect(url_for('kyc_route'))
    return redirect(url_for('login'))

@app.route('/logs')
def get_logs():
    return jsonify(log_buffer)

@app.route('/kyc', methods=['GET'])
def kyc_route():
    return kyc()

@app.route('/kyc/verifier_data/<user_id>/<filename>')
def serve_kyc_file_route(user_id, filename):
    return serve_kyc_file(user_id, filename)

@app.route('/kyc/download_excel')
def download_kyc_excel_route():
    return download_kyc_excel()

@app.route('/kyc/download_pdf_all')
def download_pdf_all_route():
    return download_pdf_all()

@app.route('/kyc/download_pdf/<user_id>')
def download_user_pdf_route(user_id):
    return download_user_pdf(user_id)

@app.route('/kyc/download_json')
def download_kyc_json_route():
    return download_kyc_json()

@app.route('/kyc/download_all_zips')
def download_kyc_all_zips_route():
    return download_kyc_all_zips()

def datetimeformat(value):
    if value and isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
            return dt.strftime('%d.%m.%Y | %H:%M:%S')
        except ValueError:
            return value
    return ''
app.jinja_env.filters['datetimeformat'] = datetimeformat

if __name__ == '__main__':
    app.run(debug=True, host=config.FLASK_HOST, port=config.FLASK_PORT)