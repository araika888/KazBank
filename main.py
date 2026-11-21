#1.PostgreSQL server version.
# import psycopg

# conn_str = "host=localhost dbname=postgres user=postgres password=arai260807"

# with psycopg.connect(conn_str) as conn:
#     with conn.cursor() as cur:
#         cur.execute("SELECT version()")
#         row = cur.fetchone()
#         print(row[0])


#2.Load the connection string from a .env file using python-dotenv
# import psycopg
# from dotenv import load_dotenv
# import os

# # Загружаем данные из .env
# load_dotenv()

# # Получаем строку подключения
# conn_str = os.getenv("DATABASE_URL")

# # Подключаемся к PostgreSQL
# with psycopg.connect(conn_str) as conn:
#     with conn.cursor() as cur:
#         cur.execute("SELECT version()")
#         row = cur.fetchone()
#         print(row[0])

# #3.Confirm autocommit=False is the default by checking conn.autocommit
# import psycopg
# from dotenv import load_dotenv
# import os

# load_dotenv()

# conn_str = os.getenv("DATABASE_URL")

# with psycopg.connect(conn_str) as conn:
#     print("Autocommit:", conn.autocommit)

#     with conn.cursor() as cur:
#         cur.execute("SELECT version()")
#         row = cur.fetchone()
#         print(row[0])

#step 2
import psycopg
from dotenv import load_dotenv
import os

# Load database connection settings
load_dotenv()
conn_str = os.getenv("DATABASE_URL")

if not conn_str:
    raise ValueError("DATABASE_URL not found in .env file")


# STEP 2.1 — CREATE TABLES

DDL = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    city TEXT DEFAULT 'Almaty'
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    account_number TEXT UNIQUE NOT NULL,
    balance NUMERIC(15, 2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(account_id),
    transaction_type TEXT NOT NULL
        CHECK (transaction_type IN ('debit', 'credit')),
    amount NUMERIC(15, 2) NOT NULL CHECK (amount > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


# STEP 2.2 — SEED DATA

SEED_CUSTOMERS = [
    ("Arman Bekov", "Almaty"),
    ("Zarina Seiit", "Astana"),
    ("Daniyar Nurlan", "Shymkent"),
    ("Aigerim Sadyk", "Almaty"),
    ("Dias Omarov", "Aktau"),
    ("Madina Askar", "Astana"),
    ("Nursultan Ali", "Almaty"),
    ("Aruzhan Kairat", "Karaganda"),
    ("Timur Bek", "Shymkent"),
    ("Amina Serik", "Aktobe"),
]

SEED_ACCOUNTS = [
    ("Arman Bekov", "KZ100001", 150000),
    ("Arman Bekov", "KZ100002", 250000),
    ("Zarina Seiit", "KZ100003", 300000),
    ("Daniyar Nurlan", "KZ100004", 120000),
    ("Daniyar Nurlan", "KZ100005", 50000),
    ("Aigerim Sadyk", "KZ100006", 400000),
    ("Dias Omarov", "KZ100007", 80000),
    ("Madina Askar", "KZ100008", 220000),
    ("Madina Askar", "KZ100009", 100000),
    ("Nursultan Ali", "KZ100010", 350000),
    ("Aruzhan Kairat", "KZ100011", 175000),
    ("Timur Bek", "KZ100012", 90000),
    ("Timur Bek", "KZ100013", 60000),
    ("Amina Serik", "KZ100014", 500000),
    ("Amina Serik", "KZ100015", 70000),
]


# STEP 2.3 — CREATE TABLES AND INSERT DATA

with psycopg.connect(conn_str) as conn:

    conn.execute(DDL)
    print("Three tables created successfully!")

    cur = conn.cursor()

    # Insert 10 customers using executemany()
    cur.executemany(
        """
        INSERT INTO customers (full_name, city)
        SELECT %s, %s
        WHERE NOT EXISTS (
            SELECT 1 FROM customers
            WHERE full_name = %s AND city = %s
        )
        """,
        [
            (name, city, name, city)
            for name, city in SEED_CUSTOMERS
        ],
    )
    print("Customers inserted!")

    # Insert 15 accounts using executemany()
    cur.executemany(
        """
        INSERT INTO accounts (customer_id, account_number, balance)
        SELECT customer_id, %s, %s
        FROM customers
        WHERE full_name = %s
        ON CONFLICT (account_number) DO NOTHING
        """,
        [
            (account_number, balance, customer_name)
            for customer_name, account_number, balance in SEED_ACCOUNTS
        ],
    )
    print("Accounts inserted!")

    conn.commit()


# STEP 2.4 — VERIFY DATA

with psycopg.connect(conn_str) as conn:

    customers_count = conn.execute(
        "SELECT COUNT(*) FROM customers"
    ).fetchone()[0]

    accounts_count = conn.execute(
        "SELECT COUNT(*) FROM accounts"
    ).fetchone()[0]

    print("Number of customers:", customers_count)
    print("Number of accounts:", accounts_count)


# STEP 2.5 — TEST UNIQUE CONSTRAINT

try:
    with psycopg.connect(conn_str) as conn:
        conn.execute(
            """
            INSERT INTO accounts (customer_id, account_number, balance)
            SELECT customer_id, 'KZ100001', 100000
            FROM customers
            LIMIT 1
            """
        )
        conn.commit()

except psycopg.errors.UniqueViolation:
    print("UNIQUE constraint works! Duplicate account number rejected.")

else:
    print("ERROR: UNIQUE constraint does not work!")


print("STEP 2 COMPLETED!")
