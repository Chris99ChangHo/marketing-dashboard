# config.py: Configuration settings for the backend application
#
# This file centralizes all configuration settings for the Flask backend application.
# It loads environment variables from a .env file and defines various parameters
# for Google Analytics, SERanking, WordPress authentication, Flask environment,
# and PDF font management. This ensures that all critical settings are managed
# from a single source, promoting consistency and ease of maintenance.
#
# Dependencies:
# - python-dotenv (for loading environment variables)
# - Standard library modules: os, pathlib
#
# Key Sections:
# - Google Analytics settings: API client files and property ID.
# - SERanking API settings: API key and base URL.
# - WordPress auth settings: URLs and credentials for WordPress integration.
# - Flask environment settings: FLASK_ENV, secret keys for Flask and JWT.
# - New WordPress API Settings for Dynamic PDF Covers: Category IDs and API base URL.
# - Font Management Configuration: Base paths and specific font file paths for PDF generation.
#
# Key Functions:
# - validate_fonts(): Verifies the existence of all configured font files.
# - get_font_info(): Returns a dictionary of current font configuration details.

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Google Analytics settings ---
CLIENT_SECRET_FILE = os.path.join(os.path.dirname(__file__), 'client_secret.json')
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')
SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']

# --- SERanking API settings ---
SERANKING_API_KEY = os.getenv("SERANKING_API_KEY")
SERANKING_BASE_URL = os.getenv('SERANKING_BASE_URL', 'https://api4.seranking.com')

# --- WordPress auth settings ---
WORDPRESS_API_BASE_URL = os.getenv('WORDPRESS_API_BASE_URL', 'https://gnaemarketing.com.au/wp-json/wp/v2')
WORDPRESS_AUTH_URL = os.getenv("WORDPRESS_AUTH_URL", "https://gnaemarketing.com.au/report/wp-admin")

# --- Flask environment settings ---
FLASK_ENV = os.getenv('FLASK_ENV', 'development')  # development, production
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

# Multi-tenant GA4 settings
GA4_MULTI_TENANT = os.getenv('GA4_MULTI_TENANT', 'false').lower() == 'true'
# 주의: ga4_service가 숫자만 기대한다고 가정. 필요시 "properties/NNN" 형태와 통일.
DEV_GA4_PROPERTY_ID = os.getenv('DEV_GA4_PROPERTY_ID', '435338953')
CLIENTS_REGISTRY_PATH = os.getenv('CLIENTS_REGISTRY_PATH', os.path.join(os.path.dirname(__file__), 'clients.json'))

# --- New WordPress API Settings for Dynamic PDF Covers ---
PDF_COVER_CATEGORY_ID = os.getenv('PDF_COVER_CATEGORY_ID', '3')
PDF_BACK_COVER_CATEGORY_ID = os.getenv('PDF_BACK_COVER_CATEGORY_ID', '4')

# WordPress API Authentication (for fetching media)
WP_API_USERNAME = os.getenv('WP_API_USERNAME')
WP_API_APPLICATION_PASSWORD = os.getenv('WP_API_APPLICATION_PASSWORD')

# --- Font Management Configuration ---
PROJECT_ROOT = Path(__file__).parent
PRODUCTION_DOMAIN = 'dashboard.dev1.gnasolutions.com.au'

if FLASK_ENV == 'development':
    FONT_BASE_PATH = Path("C:/Users/awake/Documents/changho/marketing-dashboard/backend/static/fonts")
    _jwt_cookie_domain = None
else:
    FONT_BASE_PATH = Path("/home/dev1gna/public_html/dashboard.dev1.gnasolutions.com.au/static/fonts")
    _jwt_cookie_domain = PRODUCTION_DOMAIN

JWT_COOKIE_DOMAIN = _jwt_cookie_domain
JWT_COOKIE_PATH = '/'

FONT_PATHS = {
    'noto_sans': FONT_BASE_PATH / "NotoSans-Regular.ttf",
    'noto_sans_kr': FONT_BASE_PATH / "NotoSansKR-Regular.ttf",
    'noto_sans_sc': FONT_BASE_PATH / "NotoSansSC-Regular.ttf",
}

def validate_fonts():
    missing_fonts = []
    if not FONT_BASE_PATH.exists():
        raise FileNotFoundError(f"Font directory does not exist: {FONT_BASE_PATH}")
    for font_name, font_path in FONT_PATHS.items():
        if not font_path.exists():
            missing_fonts.append(f"{font_name}: {font_path}")
    if missing_fonts:
        error_message = "Missing font files:\n" + "\n".join([f"  - {font}" for font in missing_fonts])
        error_message += f"\n\nPlease ensure all Noto Sans font files are uploaded to: {FONT_BASE_PATH}"
        raise FileNotFoundError(error_message)
    return True

def get_font_info():
    return {
        'environment': FLASK_ENV,
        'font_base_path': str(FONT_BASE_PATH),
        'font_paths': {name: str(path) for name, path in FONT_PATHS.items()},
        'fonts_exist': all(path.exists() for path in FONT_PATHS.values())
    }