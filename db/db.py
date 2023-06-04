import os
import psycopg2


def connect():
    # Connect to the PostgreSQL databas
    conn = psycopg2.connect(
        host=os.environ.get("SQL_HOST", "localhost"),
        database=os.environ.get("SQL_USER", "postgres"),
        user=os.environ.get("SQL_USER", "postgres"),
        password=os.environ.get("SQL_PASSWORD", "postgres")
    )

    cur = conn.cursor()
    return conn, cur


def close(conn, cur):
    cur.close()
    conn.close()
