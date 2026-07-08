 CREATE DATABASE IF NOT EXISTS customer_service
 CHARACTER SET utf8mb4
 COLLATE utf8mb4_unicode_ci;
 USE customer_service;
 CREATE TABLE conversations (
   id INT PRIMARY KEY AUTO_INCREMENT,
   session_id VARCHAR(255) UNIQUE NOT NULL,
   user_id VARCHAR(255) NOT NULL,
   user_name VARCHAR(255),
   channel VARCHAR(50) DEFAULT 'web',
   status ENUM('active', 'closed') DEFAULT 'active',
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
   INDEX idx_user_id (user_id),
   INDEX idx_status (status),
   INDEX idx_created_at (created_at)
 ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
 CREATE TABLE messages (
   id INT PRIMARY KEY AUTO_INCREMENT,
   conversation_id INT NOT NULL,
   role ENUM('user', 'assistant') NOT NULL,
   content TEXT NOT NULL,
   message_metadata JSON,
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   INDEX idx_conversation (conversation_id),
   INDEX idx_created_at (created_at),
   FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
 ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
 CREATE TABLE knowledge_files (
   id BIGINT PRIMARY KEY AUTO_INCREMENT,
   original_filename VARCHAR(500) NOT NULL,
   file_type VARCHAR(20) NOT NULL,
   file_hash VARCHAR(64) UNIQUE NOT NULL,
   file_size BIGINT NOT NULL,
   parse_mode ENUM('chunk', 'qa') NOT NULL,
   chunk_count INT DEFAULT 0,
   image_count INT DEFAULT 0,
   status ENUM('uploading', 'processing', 'ready', 'failed') DEFAULT 'uploading',
   error_message TEXT,
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
 ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
