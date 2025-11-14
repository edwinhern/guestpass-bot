-- V1: Initial schema for guest parking registrations
-- Creates registrations table with all required fields for tracking parking passes

CREATE TABLE IF NOT EXISTS registrations (
    id SERIAL PRIMARY KEY,
    discord_user_id VARCHAR(255) NOT NULL,

    -- Personal Information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,

    -- Vehicle Information
    license_plate VARCHAR(20) NOT NULL,
    license_plate_state VARCHAR(2) NOT NULL,
    car_year VARCHAR(4) NOT NULL,
    car_make VARCHAR(50) NOT NULL,
    car_model VARCHAR(50) NOT NULL,
    car_color VARCHAR(30) NOT NULL,

    -- Visit Information
    resident_visiting VARCHAR(100) NOT NULL,
    apartment_visiting VARCHAR(20) NOT NULL,

    -- Contact Information (optional)
    phone_number VARCHAR(20),
    email VARCHAR(255) NOT NULL,

    -- Tracking Information
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_submitted_at TIMESTAMP,
    expires_at TIMESTAMP,
    submission_count INTEGER NOT NULL DEFAULT 0,
    auto_reregister BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT FALSE
);

-- Create indexes for efficient searching
CREATE INDEX idx_registrations_discord_user_id ON registrations(discord_user_id);
CREATE INDEX idx_registrations_first_name ON registrations(first_name);
CREATE INDEX idx_registrations_last_name ON registrations(last_name);
CREATE INDEX idx_registrations_license_plate ON registrations(license_plate);
CREATE INDEX idx_registrations_car_model ON registrations(car_model);
CREATE INDEX idx_registrations_expires_at ON registrations(expires_at);
CREATE INDEX idx_registrations_is_active ON registrations(is_active);
CREATE INDEX idx_registrations_auto_reregister ON registrations(auto_reregister);

-- Create composite index for common search patterns
CREATE INDEX idx_registrations_search ON registrations(first_name, last_name, car_model);
