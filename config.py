try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os
from datetime import timedelta

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://sebastianrague@localhost:5432/mydb')

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY') or os.getenv('FLASK_SECRET_KEY')
if not JWT_SECRET_KEY and os.getenv('FLASK_ENV', 'development') == 'production':
    raise EnvironmentError('JWT_SECRET_KEY must be set in production')
JWT_SECRET_KEY = JWT_SECRET_KEY or 'change-this-secret'

JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv('JWT_EXPIRES_HOURS', '24')))
EMAIL_TOKEN_EXPIRES_HOURS = int(os.getenv('EMAIL_TOKEN_EXPIRES_HOURS', '24'))
PASSWORD_RESET_EXPIRES_HOURS = int(os.getenv('PASSWORD_RESET_EXPIRES_HOURS', '2'))
