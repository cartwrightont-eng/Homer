import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

from config import DATABASE_URL

_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        _pool = pool.SimpleConnectionPool(minconn=1, maxconn=10, dsn=DATABASE_URL)
    return _pool


def get_connection():
    return _get_pool().getconn()


def return_connection(conn):
    if _pool is not None and conn is not None:
        _pool.putconn(conn)


@contextmanager
def db_cursor(cursor_factory=RealDictCursor, commit=False):
    conn = get_connection()
    try:
        conn.cursor().execute('SELECT 1')
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        _get_pool().putconn(conn)
        conn = _get_pool().getconn()
    cursor = conn.cursor(cursor_factory=cursor_factory)
    try:
        yield conn, cursor
        if commit:
            conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        return_connection(conn)