import psycopg2

DB_CONFIG = {
    "dbname": "Hotel",
    "user": "postgres",
    "password": "1234",
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)