import sqlite3
from datetime import datetime
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.setup_database()
        
    def setup_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vehicle_owners (
                    license_plate TEXT PRIMARY KEY,
                    owner_name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    address TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_plate TEXT,
                    violation_type TEXT,
                    fine_amount REAL,
                    date_time TIMESTAMP,
                    image_path TEXT,
                    processed BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (license_plate) REFERENCES vehicle_owners(license_plate)
                )
            ''')
            
            conn.commit()
            
    def add_vehicle_owner(self, owner_data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO vehicle_owners
                (license_plate, owner_name, email, phone, address)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                owner_data['license_plate'],
                owner_data['owner_name'],
                owner_data['email'],
                owner_data['phone'],
                owner_data['address']
            ))
            conn.commit()
            
    def get_owner_details(self, license_plate):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM vehicle_owners
                WHERE license_plate = ?
            ''', (license_plate,))
            return cursor.fetchone()
            
    def record_violation(self, violation_data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO violations
                (license_plate, violation_type, fine_amount, date_time, image_path)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                violation_data['license_plate'],
                violation_data['violation_type'],
                violation_data['fine_amount'],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                violation_data['image_path']
            ))
            violation_id = cursor.lastrowid
            conn.commit()
            return violation_id
            
    def get_violations(self, processed=False):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT v.*, o.owner_name, o.email
                FROM violations v
                JOIN vehicle_owners o ON v.license_plate = o.license_plate
                WHERE v.processed = ?
            ''', (processed,))
            return cursor.fetchall()
            
    def mark_violation_processed(self, violation_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE violations
                SET processed = TRUE
                WHERE id = ?
            ''', (violation_id,))
            conn.commit()