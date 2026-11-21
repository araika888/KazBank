#1.PostgreSQL server version.
import psycopg

conn_str = "host=localhost dbname=postgres user=postgres password=arai260807"

with psycopg.connect(conn_str) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT version()")
        row = cur.fetchone()
        print(row[0])

#2.Load the connection string from a .env file using python-dotenv
import psycopg
from dotenv import load_dotenv
import os

# Загружаем данные из .env
load_dotenv()

# Получаем строку подключения
conn_str = os.getenv("DATABASE_URL")

# Подключаемся к PostgreSQL
with psycopg.connect(conn_str) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT version()")
        row = cur.fetchone()
        print(row[0])

#3.Confirm autocommit=False is the default by checking conn.autocommit
import psycopg
from dotenv import load_dotenv
import os

load_dotenv()

conn_str = os.getenv("DATABASE_URL")

with psycopg.connect(conn_str) as conn:
    print("Autocommit:", conn.autocommit)

    with conn.cursor() as cur:
        cur.execute("SELECT version()")
        row = cur.fetchone()
        print(row[0])