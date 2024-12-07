-- Initialize Database Schema

-- Create vehicle owners table
CREATE TABLE IF NOT EXISTS vehicle_owners (
    license_plate TEXT PRIMARY KEY,
    owner_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create violations table
CREATE TABLE IF NOT EXISTS violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    license_plate TEXT,
    violation_type TEXT NOT NULL,
    fine_amount REAL NOT NULL,
    location TEXT,
    image_path TEXT,
    processed BOOLEAN DEFAULT FALSE,
    notification_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (license_plate) REFERENCES vehicle_owners(license_plate)
);

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    violation_id INTEGER,
    notification_type TEXT NOT NULL,
    recipient_email TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    last_attempt TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (violation_id) REFERENCES violations(id)
);

-- Create payment records table
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    violation_id INTEGER,
    amount REAL NOT NULL,
    payment_method TEXT NOT NULL,
    transaction_id TEXT,
    status TEXT DEFAULT 'pending',
    payment_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (violation_id) REFERENCES violations(id)
);

-- Create indexes
CREATE INDEX idx_violations_license_plate ON violations(license_plate);
CREATE INDEX idx_violations_created_at ON violations(created_at);
CREATE INDEX idx_notifications_violation_id ON notifications(violation_id);
CREATE INDEX idx_payments_violation_id ON payments(violation_id);

-- Create views
CREATE VIEW violation_summary AS
SELECT 
    v.id as violation_id,
    v.violation_type,
    v.fine_amount,
    v.created_at as violation_date,
    vo.license_plate,
    vo.owner_name,
    vo.email,
    CASE 
        WHEN p.status = 'completed' THEN 'paid'
        ELSE 'unpaid'
    END as payment_status
FROM violations v
LEFT JOIN vehicle_owners vo ON v.license_plate = vo.license_plate
LEFT JOIN payments p ON v.id = p.violation_id;