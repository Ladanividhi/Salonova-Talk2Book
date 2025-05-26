import sqlite3
import os

def init_database():
    # Ensure the data directory exists
    os.makedirs("backend/data", exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect("backend/data/salonova.db")
    cursor = conn.cursor()

    # Create salons table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS salons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        address TEXT,
        phone TEXT,
        email TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create services table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        duration INTEGER,  -- duration in minutes
        price DECIMAL(10,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create appointments table with proper constraints and relationships
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        salon_id INTEGER,
        service_id INTEGER,
        customer_name TEXT NOT NULL,
        customer_email TEXT NOT NULL,
        appointment_date DATE NOT NULL,
        start_time TIME NOT NULL,
        end_time TIME NOT NULL,
        status TEXT CHECK(status IN ('pending', 'confirmed', 'cancelled', 'completed')) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        FOREIGN KEY (salon_id) REFERENCES salons(id),
        FOREIGN KEY (service_id) REFERENCES services(id)
    )
    ''')

    # Create trigger to update updated_at timestamp
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS appointments_updated_at 
    AFTER UPDATE ON appointments
    BEGIN
        UPDATE appointments SET updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.id;
    END;
    ''')

    # Insert some sample salons
    cursor.execute('''
    INSERT OR IGNORE INTO salons (name, address, phone, email) VALUES 
    ('StyleSalon', '123 Main St', '555-0101', 'style@salon.com'),
    ('BeautyHub', '456 Park Ave', '555-0102', 'beauty@hub.com'),
    ('HairArt', '789 Oak Rd', '555-0103', 'hair@art.com')
    ''')

    # Insert some sample services
    cursor.execute('''
    INSERT OR IGNORE INTO services (name, description, duration, price) VALUES 
    ('Haircut', 'Basic haircut and styling', 30, 35.00),
    ('Massage', 'Full body relaxation massage', 60, 75.00),
    ('Manicure', 'Basic manicure with polish', 45, 25.00)
    ''')

    # Create index for faster appointment lookups
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_appointments_datetime 
    ON appointments(appointment_date, start_time)
    ''')

    # Commit and close
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_database()
    print("Database initialized successfully!") 