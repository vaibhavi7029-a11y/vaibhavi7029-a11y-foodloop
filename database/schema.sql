-- =========================================
-- FOODLOOP DATABASE
-- =========================================

CREATE DATABASE IF NOT EXISTS foodloop;

USE foodloop;


-- =========================================
-- 1. USERS
-- =========================================

CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('ADMIN', 'RESTAURANT', 'NGO', 'VOLUNTEER') NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================================
-- 2. ORGANIZATIONS
-- =========================================

CREATE TABLE IF NOT EXISTS organizations (
    organization_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(150) NOT NULL,
    organization_type ENUM('RESTAURANT', 'NGO') NOT NULL,
    owner_user_id INT,
    phone VARCHAR(20),
    email VARCHAR(150),
    address VARCHAR(255),
    city VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (owner_user_id)
        REFERENCES users(user_id)
        ON DELETE SET NULL
);


-- =========================================
-- 3. LOCATIONS
-- =========================================

CREATE TABLE IF NOT EXISTS locations (
    location_id INT PRIMARY KEY AUTO_INCREMENT,
    address VARCHAR(255),
    city VARCHAR(100),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8)
);


-- =========================================
-- 4. FOOD DONATIONS
-- =========================================

CREATE TABLE IF NOT EXISTS food_donations (
    donation_id INT PRIMARY KEY AUTO_INCREMENT,

    organization_id INT NOT NULL,

    food_name VARCHAR(150) NOT NULL,
    food_type VARCHAR(100),

    quantity INT NOT NULL,

    quantity_unit ENUM(
        'MEALS',
        'KG',
        'PACKETS',
        'PLATES'
    ) DEFAULT 'MEALS',

    preparation_time DATETIME,
    available_until DATETIME,

    description TEXT,
    image_path VARCHAR(255),

    location_id INT,

    status ENUM(
        'AVAILABLE',
        'REQUESTED',
        'PICKED_UP',
        'COMPLETED',
        'EXPIRED',
        'CANCELLED'
    ) DEFAULT 'AVAILABLE',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (organization_id)
        REFERENCES organizations(organization_id)
        ON DELETE CASCADE,

    FOREIGN KEY (location_id)
        REFERENCES locations(location_id)
        ON DELETE SET NULL
);


-- =========================================
-- 5. FOOD REQUESTS
-- =========================================

CREATE TABLE IF NOT EXISTS food_requests (
    request_id INT PRIMARY KEY AUTO_INCREMENT,

    donation_id INT NOT NULL,

    ngo_organization_id INT NOT NULL,

    requested_quantity INT NOT NULL,

    status ENUM(
        'PENDING',
        'APPROVED',
        'REJECTED',
        'CANCELLED',
        'COMPLETED'
    ) DEFAULT 'PENDING',

    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (donation_id)
        REFERENCES food_donations(donation_id)
        ON DELETE CASCADE,

    FOREIGN KEY (ngo_organization_id)
        REFERENCES organizations(organization_id)
        ON DELETE CASCADE
);


-- =========================================
-- 6. PICKUPS
-- =========================================

CREATE TABLE IF NOT EXISTS pickups (
    pickup_id INT PRIMARY KEY AUTO_INCREMENT,

    request_id INT NOT NULL,

    volunteer_user_id INT,

    pickup_time DATETIME,

    delivery_time DATETIME,

    status ENUM(
        'ASSIGNED',
        'ON_THE_WAY',
        'COLLECTED',
        'DELIVERED',
        'CANCELLED'
    ) DEFAULT 'ASSIGNED',

    notes TEXT,

    FOREIGN KEY (request_id)
        REFERENCES food_requests(request_id)
        ON DELETE CASCADE,

    FOREIGN KEY (volunteer_user_id)
        REFERENCES users(user_id)
        ON DELETE SET NULL
);


-- =========================================
-- 7. FEEDBACK
-- =========================================

CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INT PRIMARY KEY AUTO_INCREMENT,

    request_id INT NOT NULL,

    user_id INT NOT NULL,

    rating INT CHECK (rating BETWEEN 1 AND 5),

    comment TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (request_id)
        REFERENCES food_requests(request_id)
        ON DELETE CASCADE,

    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);


-- =========================================
-- 8. SUBSCRIPTIONS
-- =========================================

CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id INT PRIMARY KEY AUTO_INCREMENT,

    organization_id INT NOT NULL,

    plan ENUM(
        'FREE',
        'PRO',
        'ENTERPRISE'
    ) DEFAULT 'FREE',

    start_date DATE,

    end_date DATE,

    status ENUM(
        'ACTIVE',
        'EXPIRED',
        'CANCELLED'
    ) DEFAULT 'ACTIVE',

    FOREIGN KEY (organization_id)
        REFERENCES organizations(organization_id)
        ON DELETE CASCADE
);


-- =========================================
-- 9. ADMIN USER
-- =========================================

INSERT INTO users
(
    name,
    email,
    password,
    role,
    phone
)
SELECT
    'FoodLoop Admin',
    'admin@foodloop.com',
    'scrypt:32768:8:1$EiCA9wWfyCr5IGfM$8db147805f3fd7701e9bb4c8c4560c934bd1d7224ff5fd35e5784bdc71f9d3de895a7bead8c60efb7ebe676f9d6fd500728bc117207f8213211f2e744749524b',
    'ADMIN',
    '9999999999'
WHERE NOT EXISTS (
    SELECT 1
    FROM users
    WHERE email = 'admin@foodloop.com'
);


-- =========================================
-- 10. CHECK ALL TABLES
-- =========================================

SHOW TABLES;


-- =========================================
-- 11. CHECK ADMIN
-- =========================================

SELECT
    user_id,
    name,
    email,
    role,
    phone,
    created_at
FROM users
WHERE email = 'admin@foodloop.com';