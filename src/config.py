import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

VERIFIER_DB_PATH = os.path.join(PROJECT_ROOT, 'Verifier_bot', 'verifier_data.db')
BASE_DIRECTORY = os.path.join(PROJECT_ROOT, 'Verifier_bot', 'verifier_data')
TEMPLATE_DIR = os.path.join(CURRENT_DIR, 'templates')
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5001
SECRET_KEY = "mysecret"

STATIC_DIR = os.path.join(CURRENT_DIR, 'static')

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"
