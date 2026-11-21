# KazBank Transaction API

A small REST API for a fictional bank, built with **Flask** and **PostgreSQL** (via **psycopg3**).
Course project for CSCI2204 Database Management Systems, KBTU, Fall 2026.

## Features

- Schema with `customers`, `accounts` and `transactions` tables
- REST endpoints for customers, accounts, transfers and transactions
- Shared connection pool (`psycopg_pool.ConnectionPool`, min=2, max=8)
- Atomic transfers with `SERIALIZABLE` isolation and retry on `SerializationFailure`
- Explicit `COMMIT` / `ROLLBACK` in every write endpoint
- Specific error handling: `UniqueViolation` → 409, `NotNullViolation` → 400, `OperationalError` → 503
- Parameterised queries only (`%s`), so no SQL injection
- `GET /health` endpoint with pool statistics

## Requirements

- Python 3.10+
- PostgreSQL 15+

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/araika888/KazBank.git
cd KazBank
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Create the database

```bash
psql -U postgres -c "CREATE DATABASE kazbank;"
```

### 4. Configure environment variables

Create a `.env` file in the project root (it is listed in `.gitignore` and is never committed):

```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/kazbank
```

### 5. Create the schema and seed data

```bash
python main.py
```

> Adjust this step if your schema/seed script has a different name.

### 6. Run the API

```bash
python run.py
```

The server starts at `http://127.0.0.1:5000`.

## Project structure

```
app/            Flask application (app factory, DB helpers, routes)
database/       SQL / schema and seed files
main.py         Schema creation and seeding script
run.py          Entry point that starts the Flask server
requirements.txt
```

## API endpoints

| Method | Endpoint                       | Description                              | Success |
| ------ | ------------------------------ | ---------------------------------------- | ------- |
| GET    | `/customers`                   | List all customers (`?city=` to filter)  | 200     |
| POST   | `/customers`                   | Create a customer                        | 201     |
| GET    | `/accounts?customer_id=<n>`    | List accounts of a customer              | 200     |
| POST   | `/transfer`                    | Transfer funds between two accounts      | 200     |
| GET    | `/transactions?account_id=<n>` | List transactions of an account          | 200     |
| GET    | `/health`                      | Database and connection pool status      | 200     |

### Error codes

| Status | Meaning                                              |
| ------ | ---------------------------------------------------- |
| 400    | Missing or invalid field (`NotNullViolation`)        |
| 404    | Resource not found                                   |
| 409    | Duplicate value (`UniqueViolation`)                  |
| 503    | Database unavailable (`OperationalError`)            |

## Sample requests (curl)

List customers:

```bash
curl http://127.0.0.1:5000/customers
```

Search customers by city:

```bash
curl "http://127.0.0.1:5000/customers?city=Almaty"
```

Create a customer:

```bash
curl -X POST http://127.0.0.1:5000/customers \
  -H "Content-Type: application/json" \
  -d '{"full_name": "Aigerim Sadykova", "city": "Almaty"}'
```

List accounts of customer 1:

```bash
curl "http://127.0.0.1:5000/accounts?customer_id=1"
```

Transfer funds:

```bash
curl -X POST http://127.0.0.1:5000/transfer \
  -H "Content-Type: application/json" \
  -d '{"from_account": 1, "to_account": 2, "amount": 5000}'
```

List transactions of account 1:

```bash
curl "http://127.0.0.1:5000/transactions?account_id=1"
```

Health check:

```bash
curl http://127.0.0.1:5000/health
```

> On Windows `cmd`, use double quotes with escaped inner quotes for the JSON body,
> or use Git Bash / PowerShell / Postman.

## SQL injection test

Parameterised queries treat the input as data, so this request returns an empty list
instead of dumping the table:

```bash
curl "http://127.0.0.1:5000/customers?city=Almaty'%20OR%20'1'='1"
```

## Author

araika888