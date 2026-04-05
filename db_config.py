import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'dnyanesh',
    'database': 'Bank_system_Web_app'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)
