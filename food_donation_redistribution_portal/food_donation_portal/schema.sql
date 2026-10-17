CREATE DATABASE IF NOT EXISTS food_donation_portal
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE food_donation_portal;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(160) NOT NULL UNIQUE,
  phone VARCHAR(30),
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('Donor','NGO','Volunteer','Admin') NOT NULL DEFAULT 'Donor',
  verified TINYINT(1) NOT NULL DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS donations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  donor_id INT NOT NULL,
  food_name VARCHAR(150) NOT NULL,
  category ENUM('Cooked meal','Packaged','Produce','Bakery','Other') NOT NULL,
  quantity DECIMAL(10,2) NOT NULL,
  unit ENUM('servings','kg','boxes','packets') NOT NULL DEFAULT 'servings',
  location VARCHAR(255) NOT NULL,
  prepared_at DATETIME NOT NULL,
  safe_until DATETIME NOT NULL,
  notes TEXT,
  status ENUM('Available','Claimed','Picked up','Delivered','Cancelled') NOT NULL DEFAULT 'Available',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_donor FOREIGN KEY (donor_id) REFERENCES users(id),
  INDEX idx_available (status, safe_until)
);

CREATE TABLE IF NOT EXISTS donation_requests (
  id INT AUTO_INCREMENT PRIMARY KEY,
  donation_id INT NOT NULL,
  ngo_id INT NOT NULL,
  requested_quantity DECIMAL(10,2) NOT NULL,
  status ENUM('Pending','Approved','Rejected','Completed') NOT NULL DEFAULT 'Pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_request_donation FOREIGN KEY (donation_id) REFERENCES donations(id),
  CONSTRAINT fk_request_ngo FOREIGN KEY (ngo_id) REFERENCES users(id),
  UNIQUE KEY unique_ngo_request (donation_id, ngo_id)
);

CREATE TABLE IF NOT EXISTS deliveries (
  id INT AUTO_INCREMENT PRIMARY KEY,
  request_id INT NOT NULL UNIQUE,
  volunteer_id INT NULL,
  status ENUM('Assigned','Picked up','Delivered') NOT NULL DEFAULT 'Assigned',
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_delivery_request FOREIGN KEY (request_id) REFERENCES donation_requests(id),
  CONSTRAINT fk_delivery_volunteer FOREIGN KEY (volunteer_id) REFERENCES users(id)
);
