CREATE DATABASE IF NOT EXISTS vulntrade CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE vulntrade;

SET NAMES utf8mb4;

DROP TABLE IF EXISTS stock_price_history;
DROP TABLE IF EXISTS files;
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS holdings;
DROP TABLE IF EXISTS stocks;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  display_name VARCHAR(100) NOT NULL,
  balance BIGINT NOT NULL DEFAULT 1000000,
  role VARCHAR(20) NOT NULL DEFAULT 'user',
  bank_name VARCHAR(50) NULL,
  account_number VARCHAR(50) NULL,
  account_holder VARCHAR(50) NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE stocks (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  symbol VARCHAR(20) NOT NULL UNIQUE,
  current_price INT NOT NULL,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE stock_price_history (
  id INT AUTO_INCREMENT PRIMARY KEY,
  stock_id INT NOT NULL,
  current_price INT NOT NULL,
  recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_stock_recorded (stock_id, recorded_at),
  FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE holdings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  stock_id INT NOT NULL,
  quantity INT NOT NULL,
  avg_price INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE transactions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  type VARCHAR(50) NOT NULL,
  stock_id INT NULL,
  quantity INT NULL,
  amount BIGINT NOT NULL,
  target_user_id INT NULL,
  note VARCHAR(255) NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE posts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  title VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE comments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  post_id INT NOT NULL,
  user_id INT NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE files (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  post_id INT NOT NULL,
  original_name VARCHAR(255) NOT NULL,
  stored_name VARCHAR(255) NOT NULL,
  file_path VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO users (username, password, display_name, balance, role) VALUES
('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', '총괄관리자', 5000000, 'admin'),
('user1', 'e606e38b0d8c19b24cf0ee3808183162ea7cd63ff7912dbb22b5e803286b4446', '김민준', 1200000, 'user'),
('user2', 'e606e38b0d8c19b24cf0ee3808183162ea7cd63ff7912dbb22b5e803286b4446', '박서윤', 900000, 'user');

INSERT INTO stocks (name, symbol, current_price) VALUES
('사성전자', 'SSJ', 81200),
('SK로우닉스', 'SKL', 163500),
('현소차', 'HSC', 214000),
('현재오토네버', 'HAN', 178400),
('퀴아', 'KIA', 126500),
('두화', 'DWH', 48700),
('너희은행', 'NHB', 16200),
('둘은행', 'DBK', 9580),
('제이뱅크', 'JBK', 22400),
('인민은행', 'PMB', 13150),
('태훈테크', 'THT', 54800),
('수진바이오', 'SJB', 38200),
('은결홀딩스', 'EGH', 67400),
('희윤증권', 'HYC', 29400),
('성준건설', 'SJC', 42150),
('대한모터스', 'DHM', 58700),
('한결바이오', 'HGB', 44200),
('네오핀테크', 'NEO', 73100),
('경석네트워크', 'KSN', 95000),
('민성게임즈', 'MSG', 68000),
('승원토건', 'SWC', 42000),
('슬로우푸드', 'SLF', 31000);

INSERT INTO stock_price_history (stock_id, current_price, recorded_at) VALUES
(1, 76800, NOW() - INTERVAL 115 MINUTE),
(1, 77400, NOW() - INTERVAL 110 MINUTE),
(1, 78100, NOW() - INTERVAL 105 MINUTE),
(1, 78900, NOW() - INTERVAL 100 MINUTE),
(1, 79600, NOW() - INTERVAL 95 MINUTE),
(1, 80400, NOW() - INTERVAL 90 MINUTE),
(1, 81100, NOW() - INTERVAL 85 MINUTE),
(1, 80800, NOW() - INTERVAL 80 MINUTE),
(1, 81400, NOW() - INTERVAL 75 MINUTE),
(1, 80900, NOW() - INTERVAL 70 MINUTE),
(1, 81700, NOW() - INTERVAL 65 MINUTE),
(1, 81200, NOW() - INTERVAL 60 MINUTE),
(2, 151000, NOW() - INTERVAL 115 MINUTE),
(2, 152200, NOW() - INTERVAL 110 MINUTE),
(2, 154800, NOW() - INTERVAL 105 MINUTE),
(2, 156400, NOW() - INTERVAL 100 MINUTE),
(2, 158000, NOW() - INTERVAL 95 MINUTE),
(2, 160300, NOW() - INTERVAL 90 MINUTE),
(2, 159500, NOW() - INTERVAL 85 MINUTE),
(2, 161100, NOW() - INTERVAL 80 MINUTE),
(2, 162700, NOW() - INTERVAL 75 MINUTE),
(2, 164100, NOW() - INTERVAL 70 MINUTE),
(2, 162400, NOW() - INTERVAL 65 MINUTE),
(2, 163500, NOW() - INTERVAL 60 MINUTE),
(3, 56100, NOW() - INTERVAL 115 MINUTE),
(3, 55500, NOW() - INTERVAL 110 MINUTE),
(3, 54800, NOW() - INTERVAL 105 MINUTE),
(3, 55200, NOW() - INTERVAL 100 MINUTE),
(3, 55900, NOW() - INTERVAL 95 MINUTE),
(3, 56500, NOW() - INTERVAL 90 MINUTE),
(3, 57100, NOW() - INTERVAL 85 MINUTE),
(3, 57800, NOW() - INTERVAL 80 MINUTE),
(3, 58400, NOW() - INTERVAL 75 MINUTE),
(3, 59000, NOW() - INTERVAL 70 MINUTE),
(3, 58200, NOW() - INTERVAL 65 MINUTE),
(3, 58700, NOW() - INTERVAL 60 MINUTE),
(4, 47200, NOW() - INTERVAL 115 MINUTE),
(4, 46800, NOW() - INTERVAL 110 MINUTE),
(4, 46300, NOW() - INTERVAL 105 MINUTE),
(4, 45900, NOW() - INTERVAL 100 MINUTE),
(4, 45300, NOW() - INTERVAL 95 MINUTE),
(4, 44800, NOW() - INTERVAL 90 MINUTE),
(4, 44500, NOW() - INTERVAL 85 MINUTE),
(4, 44100, NOW() - INTERVAL 80 MINUTE),
(4, 43800, NOW() - INTERVAL 75 MINUTE),
(4, 43400, NOW() - INTERVAL 70 MINUTE),
(4, 43900, NOW() - INTERVAL 65 MINUTE),
(4, 44200, NOW() - INTERVAL 60 MINUTE),
(5, 68900, NOW() - INTERVAL 115 MINUTE),
(5, 69500, NOW() - INTERVAL 110 MINUTE),
(5, 70100, NOW() - INTERVAL 105 MINUTE),
(5, 70800, NOW() - INTERVAL 100 MINUTE),
(5, 71300, NOW() - INTERVAL 95 MINUTE),
(5, 71900, NOW() - INTERVAL 90 MINUTE),
(5, 72500, NOW() - INTERVAL 85 MINUTE),
(5, 73300, NOW() - INTERVAL 80 MINUTE),
(5, 72900, NOW() - INTERVAL 75 MINUTE),
(5, 73500, NOW() - INTERVAL 70 MINUTE),
(5, 72800, NOW() - INTERVAL 65 MINUTE),
(5, 73100, NOW() - INTERVAL 60 MINUTE);

INSERT INTO holdings (user_id, stock_id, quantity, avg_price) VALUES
(2, 1, 12, 76800),
(2, 5, 5, 70400),
(3, 2, 3, 154500);

INSERT INTO transactions (user_id, type, stock_id, quantity, amount, target_user_id, note) VALUES
(2, 'buy', 1, 12, 921600, NULL, '사성전자 매수'),
(2, 'buy', 5, 5, 352000, NULL, '네오핀테크 매수'),
(3, 'buy', 2, 3, 463500, NULL, 'SK로우닉스 매수'),
(2, 'transfer_out', NULL, NULL, 30000, 3, '스터디 정산'),
(3, 'transfer_in', NULL, NULL, 30000, 2, '스터디 정산 수신');

INSERT INTO posts (user_id, title, content) VALUES
(2, '사성전자 지금 들어가도 될까요?', '실적 기대감이 다시 붙는 것 같아요. 단기 눌림에서 잡아도 괜찮을지 궁금합니다.'),
(3, 'SK로우닉스 변동성 꽤 크네요', '오늘 흐름은 강한데 눌림도 커서 진입 타이밍이 어렵네요.'),
(1, '모의투자 서비스 안내', '실습 환경 특성상 시세는 외부 API가 아니라 내부 스케줄러 기준으로 움직입니다.');

INSERT INTO comments (post_id, user_id, content) VALUES
(1, 3, '저는 분할로 접근하는 쪽이 더 좋아 보여요.'),
(2, 2, '오늘은 거래대금이 확실히 붙는 편입니다.'),
(3, 2, '확인했습니다. 장 시작 전에 주문을 정리할게요.');
