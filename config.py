try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os
from datetime import timedelta

# ==== DATABASE CONFIGURATION ====
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise EnvironmentError(
        'DATABASE_URL environment variable must be set. '
        'Format: postgresql://user:password@host:port/database'
    )

# ==== JWT CONFIGURATION ====
FLASK_ENV = os.getenv('FLASK_ENV', 'development')

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY') or os.getenv('FLASK_SECRET_KEY')
if not JWT_SECRET_KEY:
    if FLASK_ENV == 'production':
        raise EnvironmentError(
            'JWT_SECRET_KEY environment variable must be set in production. '
            'Use a strong, random string of at least 32 characters.'
        )
    JWT_SECRET_KEY = 'dev-secret-change-in-production'

JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv('JWT_EXPIRES_HOURS', '24')))
EMAIL_TOKEN_EXPIRES_HOURS = int(os.getenv('EMAIL_TOKEN_EXPIRES_HOURS', '24'))
PASSWORD_RESET_EXPIRES_HOURS = int(os.getenv('PASSWORD_RESET_EXPIRES_HOURS', '2'))

# ==== PAGINATION CONFIGURATION ====
DEFAULT_PAGE_SIZE = int(os.getenv('DEFAULT_PAGE_SIZE', '20'))
MAX_PAGE_SIZE = int(os.getenv('MAX_PAGE_SIZE', '100'))

# ==== VALIDATION CONFIGURATION ====
MAX_PRICE = float(os.getenv('MAX_PRICE', '10000000'))  # 10 million
MAX_DISTANCE_KM = float(os.getenv('MAX_DISTANCE_KM', '100'))  # 100 km
MAX_STRING_LENGTH = int(os.getenv('MAX_STRING_LENGTH', '500'))
MAX_DESCRIPTION_LENGTH = int(os.getenv('MAX_DESCRIPTION_LENGTH', '5000'))

# ==== SECURITY CONFIGURATION ====
RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
RATE_LIMIT_PERIOD = int(os.getenv('RATE_LIMIT_PERIOD', '3600'))  # seconds
