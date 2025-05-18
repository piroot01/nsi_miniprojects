from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import sqlite3

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

DB_PATH = 'instance/database.db'

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                temperature REAL,
                timestamp_measurement TEXT,
                timestamp_sent TEXT,
                timestamp_received TEXT
            )
        ''')
        conn.commit()

def insert_measurement(temperature, timestamp_measurement, timestamp_sent):
    now = datetime.now()
    timestamp_received = now.strftime("%Y-%m-%d %H:%M:%S") + f".{now.microsecond // 1000:03d}"
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO measurements
              (temperature, timestamp_measurement, timestamp_sent, timestamp_received)
            VALUES (?, ?, ?, ?)
        ''', (temperature, timestamp_measurement, timestamp_sent, timestamp_received))
        conn.commit()

def get_all_measurements(sort='desc'):
    order = 'DESC' if sort == 'desc' else 'ASC'
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM measurements ORDER BY id {order}')
        return cursor.fetchall()


def delete_measurement(data_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM measurements WHERE id = ?', (data_id,))
        conn.commit()

def clear_measurements():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM measurements")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='measurements'")
        conn.commit()
