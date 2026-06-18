"""Utility: create a verified admin user for development.

Usage (interactive):
    python create_admin.py

Or via environment variables:
    set ADMIN_NAME=Your Name
    set ADMIN_EMAIL=you@example.com
    set ADMIN_PASSWORD=Secret123!
    python create_admin.py
"""

import os
from models import create_user
from database import get_connection


def main():
    name = os.getenv('ADMIN_NAME') or input('Admin name: ')
    email = os.getenv('ADMIN_EMAIL') or input('Admin email: ')
    password = os.getenv('ADMIN_PASSWORD') or input('Admin password: ')

    user_id = create_user(name, email, password, role='admin')

    # mark email verified so admin can log in immediately
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET email_verified=TRUE WHERE id=%s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

    print(f'Admin created: id={user_id}, email={email}')


if __name__ == '__main__':
    main()
