import sqlite3

connection = sqlite3.connect("lab_booking.db")

cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    quantity INTEGER NOT NULL,
    available INTEGER NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    equipment TEXT NOT NULL,
    date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    purpose TEXT NOT NULL,
    status TEXT DEFAULT 'Pending'
)
""")

cursor.execute("""
INSERT OR IGNORE INTO students (student_id, password)
VALUES ('STU001', '12345')
""")

cursor.execute("""
INSERT OR IGNORE INTO staff (username, password)
VALUES ('staff', 'staff123')
""")

cursor.execute("""
INSERT OR IGNORE INTO admins (username, password)
VALUES ('admin', 'admin123')
""")

equipment_list = [
    ("Digital Multimeter", 5),
    ("Oscilloscope", 3),
    ("Function Generator", 4),
    ("CRO", 2),
    ("Power Supply", 5),
    ("Signal Generator", 3)
]

for name, quantity in equipment_list:

    cursor.execute("""
    INSERT OR IGNORE INTO equipment
    (name, quantity, available)
    VALUES (?, ?, ?)
    """, (name, quantity, quantity))

connection.commit()
connection.close()

print("Database created successfully!")