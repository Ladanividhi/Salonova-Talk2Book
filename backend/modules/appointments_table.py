import sqlite3

# Connect to database (or create if it doesn't exist)
conn = sqlite3.connect("backend/data/appointments.db")
cursor = conn.cursor()

# Create appointments table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        salon_name TEXT,
        service TEXT,
        name TEXT,
        email TEXT,
        timeA TEXT,
        timeB TEXT,
        date TEXT
    )
''')

# Commit and close
conn.commit()
conn.close()

print("Appointments table created successfully!")
