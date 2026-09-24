CREATE DATABASE IF NOT EXISTS swift_gateway;
USE swift_gateway;

CREATE USER IF NOT EXISTS 'swiftapp'@'localhost' IDENTIFIED BY 'SwiftApp2024!';
GRANT ALL PRIVILEGES ON swift_gateway.* TO 'swiftapp'@'localhost';
FLUSH PRIVILEGES;

CREATE TABLE IF NOT EXISTS operators (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO operators (username, password_hash, full_name)
VALUES ('operator1', 'scrypt:32768:8:1$WkjfAlZOtRi7JOSg$8c9a3467984637b0ee01f8615773af9e59cd77767283c2668895a4246e2e5850c6dea265054090c302e5de0ceffdb980fc95ba061c76aeb0ba2cedc1173b018c', 'Sunita Rao (SWIFT Operator)')
ON DUPLICATE KEY UPDATE username = username;

CREATE TABLE IF NOT EXISTS transfers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mt103_reference VARCHAR(30) UNIQUE,
    sender_card_number VARCHAR(20) NOT NULL,
    beneficiary_name VARCHAR(100) NOT NULL,
    beneficiary_account VARCHAR(40) NOT NULL,
    beneficiary_swift_code VARCHAR(15) NOT NULL,
    beneficiary_country VARCHAR(50),
    amount DECIMAL(14,2) NOT NULL,
    currency VARCHAR(5) DEFAULT 'USD',
    status ENUM('approved','declined') NOT NULL,
    reason VARCHAR(150),
    operator_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (operator_id) REFERENCES operators(id) ON DELETE SET NULL
);

exit
