DROP TABLE IF EXISTS Account;
DROP TABLE IF EXISTS Car;
DROP TABLE IF EXISTS Booking;

CREATE TABLE Account (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(16) NOT NULL UNIQUE,
    password VARCHAR(128) NOT NULL,
    first_name VARCHAR(128) NOT NULL,
    last_name VARCHAR(128) NOT NULL,
    email VARCHAR(256) NOT NULL,
    role VARCHAR(128) NOT NULL DEFAULT 'user'
);

CREATE TABLE Car (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    make VARCHAR(32) NOT NULL,
    body_type VARCHAR(32) NOT NULL,
    colour VARCHAR(16) NOT NULL,
    seats INT UNSIGNED NOT NULL,
    location VARCHAR(64) NOT NULL,
    hourly_rate FLOAT UNSIGNED NOT NULL,
    available BOOL NOT NULL,
    latitude DOUBLE NOT NULL,
    longitude DOUBLE NOT NULL,
    car_condition BOOL NOT NULL DEFAULT 1
);

CREATE TABLE Booking (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    account_id INT UNSIGNED NOT NULL,
    car_id INT UNSIGNED NOT NULL,
    pickup_time DATETIME NOT NULL,
    hours INT UNSIGNED NOT NULL,
    amount FLOAT UNSIGNED NOT NULL,
    state ENUM ('reserved', 'in-use', 'returned', 'canceled') NOT NULL DEFAULT 'reserved'
);
