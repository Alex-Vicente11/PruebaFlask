-- Migration: Add Guest User Support
-- Date: 2025-10-23
-- Description: Adds columns to the user table to support anonymous/guest users

USE list_products;

-- Add new columns to user table
ALTER TABLE user
ADD COLUMN email VARCHAR(255) NULL UNIQUE,
ADD COLUMN password_hash VARCHAR(255) NULL,
ADD COLUMN is_guest BOOLEAN DEFAULT FALSE,
ADD COLUMN guest_id VARCHAR(100) NULL UNIQUE,
ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;

-- Create indices for better performance
CREATE INDEX idx_guest_id ON user(guest_id);
CREATE INDEX idx_is_guest ON user(is_guest);
CREATE INDEX idx_email ON user(email);

-- Update existing users to set is_guest = FALSE
UPDATE user SET is_guest = FALSE WHERE is_guest IS NULL;

-- Verify the changes
DESCRIBE user;

-- Show count of existing users
SELECT COUNT(*) AS total_users FROM user;
