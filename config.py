import os
from datetime import timedelta

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://sebastianrague@localhost:5432/mydb')

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'change-this-secret')
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv('JWT_EXPIRES_HOURS', '24')))
EMAIL_TOKEN_EXPIRES_HOURS = int(os.getenv('EMAIL_TOKEN_EXPIRES_HOURS', '24'))
PASSWORD_RESET_EXPIRES_HOURS = int(os.getenv('PASSWORD_RESET_EXPIRES_HOURS', '2'))
