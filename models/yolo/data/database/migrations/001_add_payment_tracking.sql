-- Migration: Add payment tracking
-- Version: 001
-- Date: 2024-01-01

BEGIN TRANSACTION;

-- Add payment status to violations table
ALTER TABLE violations ADD COLUMN payment_status TEXT DEFAULT 'pending';
ALTER TABLE violations ADD COLUMN payment_due_date DATE;

-- Add payment reminder settings
CREATE TABLE payment_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    violation_id INTEGER,
    reminder_type TEXT NOT NULL,
    scheduled_date DATE NOT NULL,
    sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (violation_id) REFERENCES violations(id)
);

-- Add payment statistics view
CREATE VIEW payment_statistics AS
SELECT 
    violation_type,
    COUNT(*) as total_violations,
    SUM(CASE WHEN payment_status = 'paid' THEN 1 ELSE 0 END) as paid_count,
    SUM(CASE WHEN payment_status = 'pending' THEN 1 ELSE 0 END) as pending_count,
    SUM(fine_amount) as total_fines,
    SUM(CASE WHEN payment_status = 'paid' THEN fine_amount ELSE 0 END) as collected_amount
FROM violations
GROUP BY violation_type;

COMMIT;