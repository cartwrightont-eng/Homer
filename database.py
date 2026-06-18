import psycopg2
import psycopg2.extras

from config import DATABASE_URL


def get_connection():
    conn = psycopg2.connect(dsn=DATABASE_URL)
    return conn