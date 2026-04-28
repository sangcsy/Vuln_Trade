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

INSERT INTO users (id, username, password, display_name, balance, role) VALUES
(1, 'vuln@admin', '5206b8b8a996cf5320cb12ca91c7b790fba9f030408efe83ebb83548dc3007bd', '총괄관리자', 5000000, 'admin');

INSERT INTO users (id, username, password, display_name, balance, role)
WITH RECURSIVE mock_users(n) AS (
  SELECT 1
  UNION ALL
  SELECT n + 1 FROM mock_users WHERE n < 200
)
SELECT
  n + 1,
  CONCAT('user', n),
  CASE WHEN n = 162 THEN SHA2('password1!', 256) ELSE SHA2(CONCAT('VulnTrade!', n, '#', LPAD(n, 3, '0')), 256) END,
  CONCAT('모의투자자', LPAD(n, 3, '0')),
  CASE WHEN n = 162 THEN 45600000000 ELSE 800000 + (n * 15700) END,
  'user'
FROM mock_users;

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

INSERT INTO transactions (user_id, type, stock_id, quantity, amount, target_user_id, note, created_at) VALUES
(163, 'transfer_out', NULL, NULL, 300000000, 18, '프라임 블록딜 정산', NOW() - INTERVAL 11 MINUTE),
(18, 'transfer_in', NULL, NULL, 300000000, 163, '프라임 블록딜 정산 수신', NOW() - INTERVAL 11 MINUTE),
(44, 'transfer_out', NULL, NULL, 120000000, 163, '장외 매각 대금', NOW() - INTERVAL 24 MINUTE),
(163, 'transfer_in', NULL, NULL, 120000000, 44, '장외 매각 대금 수신', NOW() - INTERVAL 24 MINUTE),
(163, 'transfer_out', NULL, NULL, 250000000, 78, '고액 담보 이체', NOW() - INTERVAL 37 MINUTE),
(78, 'transfer_in', NULL, NULL, 250000000, 163, '고액 담보 이체 수신', NOW() - INTERVAL 37 MINUTE),
(121, 'transfer_out', NULL, NULL, 180000000, 163, '투자금 회수', NOW() - INTERVAL 52 MINUTE),
(163, 'transfer_in', NULL, NULL, 180000000, 121, '투자금 회수 수신', NOW() - INTERVAL 52 MINUTE),
(163, 'transfer_out', NULL, NULL, 100000000, 139, '단기 운용금 이동', NOW() - INTERVAL 68 MINUTE),
(139, 'transfer_in', NULL, NULL, 100000000, 163, '단기 운용금 이동 수신', NOW() - INTERVAL 68 MINUTE),
(163, 'transfer_out', NULL, NULL, 275000000, 196, '기관 계좌 정산', NOW() - INTERVAL 83 MINUTE),
(196, 'transfer_in', NULL, NULL, 275000000, 163, '기관 계좌 정산 수신', NOW() - INTERVAL 83 MINUTE);

INSERT INTO posts (user_id, title, content, created_at, updated_at) VALUES
(2, '사성전자 지금 들어가도 될까요?', '실적 기대감이 다시 붙는 것 같아요. 단기 눌림에서 잡아도 괜찮을지 궁금합니다.', '2026-04-27 21:10:00', '2026-04-27 21:10:00'),
(3, 'SK로우닉스 변동성 꽤 크네요', '오늘 흐름은 강한데 눌림도 커서 진입 타이밍이 어렵네요.', '2026-04-27 14:35:00', '2026-04-27 14:35:00'),
(1, '모의투자 서비스 안내', '실습 환경 특성상 시세는 외부 API가 아니라 내부 스케줄러 기준으로 움직입니다.', '2026-04-22 08:30:00', '2026-04-22 08:30:00'),
((SELECT id FROM users WHERE username='user20'), '성준건설 차트가 삽질하다가 유전 찾은 모양입니다', '분명 아침에는 지하실로 가는 줄 알았는데 오후에 갑자기 양봉을 세웠네요. 제 계좌도 같이 굴착 중입니다.', '2026-04-26 16:42:00', '2026-04-26 16:42:00'),
((SELECT id FROM users WHERE username='user37'), '네오핀테크 매수 버튼 누르기 전 손가락 회의 결과', '엄지와 검지는 찬성, 이성은 반대했습니다. 일단 1주만 사고 제 마음의 변동성을 관찰해보겠습니다.', '2026-04-26 09:15:00', '2026-04-26 09:15:00'),
((SELECT id FROM users WHERE username='user58'), '둘은행은 이름처럼 둘 중 하나만 해줬으면 좋겠습니다', '오르거나 내리거나 둘 중 하나인데 왜 제 평단만 정확히 피해 가는지 모르겠습니다.', '2026-04-25 18:20:00', '2026-04-25 18:20:00'),
((SELECT id FROM users WHERE username='user74'), '사성전자 주주총회 대신 제 통장총회 열었습니다', '안건은 물타기 승인 여부였고 참석자 1명 만장일치로 보류됐습니다. 라면 예산이 더 중요합니다.', '2026-04-25 11:05:00', '2026-04-25 11:05:00'),
((SELECT id FROM users WHERE username='user91'), 'SK로우닉스 변동성 보고 커피 두 잔 마셨습니다', '차트가 이미 카페인 과다 섭취 상태라 저는 디카페인으로 갈아탔습니다. 그래도 눈은 못 떼겠네요.', '2026-04-24 22:48:00', '2026-04-24 22:48:00'),
((SELECT id FROM users WHERE username='user118'), '인민은행 배당 기대감으로 계산기 두드렸습니다', '계산 결과 배당보다 제가 어제 시킨 치킨값이 더 컸습니다. 장기투자의 길은 멀고 양념은 가까웠습니다.', '2026-04-24 13:30:00', '2026-04-24 13:30:00'),
((SELECT id FROM users WHERE username='user136'), '현소차 오늘 주행감 좋네요', '제 계좌는 아직 사이드브레이크가 잠겨 있는데 종목은 고속도로를 탄 것 같습니다. 탑승 타이밍이 문제네요.', '2026-04-23 20:10:00', '2026-04-23 20:10:00'),
((SELECT id FROM users WHERE username='user149'), '태훈테크 단타 치려다가 장투 선언했습니다', '매도 타이밍을 놓친 것이 아니라 투자 철학이 갑자기 깊어진 것입니다. 아무튼 그렇습니다.', '2026-04-23 12:25:00', '2026-04-23 12:25:00'),
((SELECT id FROM users WHERE username='user177'), '희윤증권 리포트 읽다가 제 잔고 리포트도 봤습니다', '투자의견은 매수인데 제 잔고 의견은 휴식입니다. 시장보다 월급날이 더 기다려집니다.', '2026-04-22 18:55:00', '2026-04-22 18:55:00'),
((SELECT id FROM users WHERE username='user194'), '슬로우푸드 이름값 제대로 하네요', '상승도 슬로우, 체결도 슬로우, 제 인내심만 패스트로 소진 중입니다. 그래도 컨셉은 확실합니다.', '2026-04-22 09:40:00', '2026-04-22 09:40:00'),
((SELECT id FROM users WHERE username='user162'), '호가창에 0이 많으면 마음도 무거워지네요', '분산투자 연습한다고 몇 종목 눌러봤는데 주문 확인 버튼 앞에서는 아직도 손이 떨립니다. 이상하게 1주씩 사는 연습보다 이체 메모 정리가 더 오래 걸리네요.', '2026-04-27 10:10:00', '2026-04-27 10:10:00');

INSERT INTO posts (user_id, title, content, created_at, updated_at) VALUES
((SELECT id FROM users WHERE username='user26'), '퀴아는 오늘 변속이 부드럽네요', '차트가 저단에서 고단으로 넘어가는 느낌입니다. 문제는 제가 아직 안전벨트만 붙잡고 있다는 점입니다.', '2026-04-26 19:05:00', '2026-04-26 19:05:00'),
((SELECT id FROM users WHERE username='user46'), '두화는 이름처럼 두 번 확인하고 들어가야겠습니다', '한 번 보고 매수하면 꼭 제 평단만 외롭게 남더라고요. 오늘은 확인 버튼 앞에서 심호흡 두 번 했습니다.', '2026-04-26 12:10:00', '2026-04-26 12:10:00'),
((SELECT id FROM users WHERE username='user67'), '제이뱅크는 앱보다 제 손익이 더 자주 튕깁니다', '핀테크라 빠를 줄 알았는데 제 수익 전환만 로그인 대기 중입니다. 비밀번호는 분명 맞는 것 같은데요.', '2026-04-25 20:35:00', '2026-04-25 20:35:00'),
((SELECT id FROM users WHERE username='user83'), '수진바이오 임상보다 제 인내심이 먼저 시험대입니다', '뉴스 하나에 심장이 반응하고 호가 하나에 손가락이 반응합니다. 바이오 투자는 체력전이네요.', '2026-04-25 08:50:00', '2026-04-25 08:50:00'),
((SELECT id FROM users WHERE username='user109'), '은결홀딩스 이름은 든든한데 제 멘탈은 홀딩 실패입니다', '장투하려고 샀는데 5분마다 확인 중입니다. 이 정도면 장투가 아니라 장시간 새로고침입니다.', '2026-04-24 19:05:00', '2026-04-24 19:05:00'),
((SELECT id FROM users WHERE username='user124'), '대한모터스 오늘 엔진 소리 괜찮네요', '시동은 걸린 것 같은데 제 계좌는 아직 주차장입니다. 출발 신호만 기다려봅니다.', '2026-04-24 09:55:00', '2026-04-24 09:55:00'),
((SELECT id FROM users WHERE username='user151'), '한결바이오는 이름처럼 한결같이 어렵습니다', '오르면 왜 올랐는지 모르겠고 내리면 왜 내렸는지 더 모르겠습니다. 그래도 관심종목에서는 못 빼겠네요.', '2026-04-23 17:45:00', '2026-04-23 17:45:00'),
((SELECT id FROM users WHERE username='user166'), '경석네트워크 연결 상태는 좋은데 제 수익은 끊겼습니다', '네트워크 종목이라 그런지 기대감은 잘 연결됩니다. 제 매도 타이밍만 계속 timeout입니다.', '2026-04-23 09:35:00', '2026-04-23 09:35:00'),
((SELECT id FROM users WHERE username='user183'), '민성게임즈 차트가 보스전 같습니다', '패턴은 보이는 것 같은데 들어가면 항상 맞습니다. 오늘도 포션 대신 물타기 버튼을 찾고 있습니다.', '2026-04-22 16:20:00', '2026-04-22 16:20:00'),
((SELECT id FROM users WHERE username='user199'), '승원토건은 천천히 쌓는 맛이 있네요', '벽돌 쌓듯 모아가려 했는데 제 조급함이 먼저 준공됐습니다. 그래도 기초공사는 튼튼해 보입니다.', '2026-04-22 11:15:00', '2026-04-22 11:15:00');

INSERT INTO comments (post_id, user_id, content) VALUES
(1, 3, '저는 분할로 접근하는 쪽이 더 좋아 보여요.'),
(2, 2, '오늘은 거래대금이 확실히 붙는 편입니다.'),
(3, 2, '확인했습니다. 장 시작 전에 주문을 정리할게요.');

INSERT INTO comments (post_id, user_id, content) VALUES
((SELECT id FROM posts WHERE title='사성전자 지금 들어가도 될까요?' LIMIT 1), (SELECT id FROM users WHERE username='user22'), '저는 들어가기 전에 항상 커피부터 삽니다. 손 떨림 방지용입니다.'),
((SELECT id FROM posts WHERE title='사성전자 지금 들어가도 될까요?' LIMIT 1), (SELECT id FROM users WHERE username='user81'), '분할 매수면 마음은 편한데 잔고가 분할되는 기분도 같이 옵니다.'),
((SELECT id FROM posts WHERE title='SK로우닉스 변동성 꽤 크네요' LIMIT 1), (SELECT id FROM users WHERE username='user44'), '이 정도 흔들림이면 차트가 아니라 놀이기구 이용권입니다.'),
((SELECT id FROM posts WHERE title='모의투자 서비스 안내' LIMIT 1), (SELECT id FROM users WHERE username='user13'), '실시간처럼 움직여서 제 심장도 실시간으로 반응 중입니다.'),
((SELECT id FROM posts WHERE title='성준건설 차트가 삽질하다가 유전 찾은 모양입니다' LIMIT 1), (SELECT id FROM users WHERE username='user63'), '저도 굴착 들어갔다가 제 평단만 매장되는 중입니다.'),
((SELECT id FROM posts WHERE title='성준건설 차트가 삽질하다가 유전 찾은 모양입니다' LIMIT 1), (SELECT id FROM users WHERE username='user142'), '유전이면 좋겠는데 제 계좌에서는 아직 흙냄새만 납니다.'),
((SELECT id FROM posts WHERE title='네오핀테크 매수 버튼 누르기 전 손가락 회의 결과' LIMIT 1), (SELECT id FROM users WHERE username='user28'), '제 손가락 회의는 늘 매수 찬성인데 회계팀이 반대합니다.'),
((SELECT id FROM posts WHERE title='둘은행은 이름처럼 둘 중 하나만 해줬으면 좋겠습니다' LIMIT 1), (SELECT id FROM users WHERE username='user105'), '오르지도 내리지도 않으면 제 감정만 상장폐지됩니다.'),
((SELECT id FROM posts WHERE title='둘은행은 이름처럼 둘 중 하나만 해줬으면 좋겠습니다' LIMIT 1), (SELECT id FROM users WHERE username='user188'), '둘 중 하나라더니 제 선택지만 늘 틀리는 게 문제네요.'),
((SELECT id FROM posts WHERE title='사성전자 주주총회 대신 제 통장총회 열었습니다' LIMIT 1), (SELECT id FROM users WHERE username='user34'), '라면 예산은 중대 사안이라 의결권 행사 신중해야 합니다.'),
((SELECT id FROM posts WHERE title='SK로우닉스 변동성 보고 커피 두 잔 마셨습니다' LIMIT 1), (SELECT id FROM users WHERE username='user156'), '저는 차트 보고 디카페인 마셨는데도 손이 떨립니다.'),
((SELECT id FROM posts WHERE title='인민은행 배당 기대감으로 계산기 두드렸습니다' LIMIT 1), (SELECT id FROM users WHERE username='user72'), '치킨 수익률은 언제나 확정 수익이라 강합니다.'),
((SELECT id FROM posts WHERE title='현소차 오늘 주행감 좋네요' LIMIT 1), (SELECT id FROM users WHERE username='user130'), '저는 아직 정류장에 있는데 종목은 톨게이트 지난 것 같습니다.'),
((SELECT id FROM posts WHERE title='현소차 오늘 주행감 좋네요' LIMIT 1), (SELECT id FROM users WHERE username='user19'), '탑승하려고 하면 꼭 급정거해서 안전벨트만 꽉 잡습니다.'),
((SELECT id FROM posts WHERE title='태훈테크 단타 치려다가 장투 선언했습니다' LIMIT 1), (SELECT id FROM users WHERE username='user51'), '장투 선언은 보통 손절 버튼을 못 봤을 때 나옵니다.'),
((SELECT id FROM posts WHERE title='희윤증권 리포트 읽다가 제 잔고 리포트도 봤습니다' LIMIT 1), (SELECT id FROM users WHERE username='user99'), '제 잔고 리포트 투자의견은 관망입니다. 아주 장기 관망입니다.'),
((SELECT id FROM posts WHERE title='슬로우푸드 이름값 제대로 하네요' LIMIT 1), (SELECT id FROM users WHERE username='user168'), '느린 건 좋은데 제 인내심만 초단타로 빠져나갑니다.'),
((SELECT id FROM posts WHERE title='슬로우푸드 이름값 제대로 하네요' LIMIT 1), (SELECT id FROM users WHERE username='user7'), '이름값 확실하네요. 수익도 천천히 오면 좋겠습니다.'),
((SELECT id FROM posts WHERE title='호가창에 0이 많으면 마음도 무거워지네요' LIMIT 1), (SELECT id FROM users WHERE username='user48'), '0이 많을수록 손가락이 공손해지는 효과가 있습니다.'),
((SELECT id FROM posts WHERE title='호가창에 0이 많으면 마음도 무거워지네요' LIMIT 1), (SELECT id FROM users WHERE username='user162'), '그래서 저는 메모를 꼼꼼히 씁니다. 나중에 제가 봐도 헷갈리더라고요.');

INSERT INTO comments (post_id, user_id, content) VALUES
((SELECT id FROM posts WHERE title='퀴아는 오늘 변속이 부드럽네요' LIMIT 1), (SELECT id FROM users WHERE username='user31'), '저는 늘 급출발했다가 급정거합니다. 운전 습관부터 고쳐야겠네요.'),
((SELECT id FROM posts WHERE title='퀴아는 오늘 변속이 부드럽네요' LIMIT 1), (SELECT id FROM users WHERE username='user88'), '안전벨트 매고 분할 탑승하면 멀미가 조금 덜합니다.'),
((SELECT id FROM posts WHERE title='두화는 이름처럼 두 번 확인하고 들어가야겠습니다' LIMIT 1), (SELECT id FROM users WHERE username='user53'), '저는 세 번 확인했는데도 제 평단이 먼저 들어가 있었습니다.'),
((SELECT id FROM posts WHERE title='제이뱅크는 앱보다 제 손익이 더 자주 튕깁니다' LIMIT 1), (SELECT id FROM users WHERE username='user117'), '수익 전환 인증번호가 제 폰에는 안 오는 것 같습니다.'),
((SELECT id FROM posts WHERE title='수진바이오 임상보다 제 인내심이 먼저 시험대입니다' LIMIT 1), (SELECT id FROM users WHERE username='user64'), '바이오는 멘탈 임상이 제일 어렵다는 말에 동의합니다.'),
((SELECT id FROM posts WHERE title='수진바이오 임상보다 제 인내심이 먼저 시험대입니다' LIMIT 1), (SELECT id FROM users WHERE username='user175'), '결과 발표 전까지 제 심박수도 같이 상장된 느낌입니다.'),
((SELECT id FROM posts WHERE title='은결홀딩스 이름은 든든한데 제 멘탈은 홀딩 실패입니다' LIMIT 1), (SELECT id FROM users WHERE username='user41'), '장투를 결심하고 3분 뒤에 차트를 켜는 게 국룰입니다.'),
((SELECT id FROM posts WHERE title='대한모터스 오늘 엔진 소리 괜찮네요' LIMIT 1), (SELECT id FROM users WHERE username='user145'), '저도 탑승 대기 중인데 제 현금이 아직 면허를 못 땄습니다.'),
((SELECT id FROM posts WHERE title='한결바이오는 이름처럼 한결같이 어렵습니다' LIMIT 1), (SELECT id FROM users WHERE username='user69'), '관심종목에서 빼면 꼭 오를 것 같아서 못 빼는 병이 있습니다.'),
((SELECT id FROM posts WHERE title='경석네트워크 연결 상태는 좋은데 제 수익은 끊겼습니다' LIMIT 1), (SELECT id FROM users WHERE username='user112'), '제 매도 버튼도 가끔 패킷 손실이 나는 것 같습니다.'),
((SELECT id FROM posts WHERE title='민성게임즈 차트가 보스전 같습니다' LIMIT 1), (SELECT id FROM users WHERE username='user132'), '저는 튜토리얼도 못 끝냈는데 난이도가 하드모드네요.'),
((SELECT id FROM posts WHERE title='민성게임즈 차트가 보스전 같습니다' LIMIT 1), (SELECT id FROM users WHERE username='user191'), '패턴 파악했다고 생각한 순간 새 페이즈 들어갑니다.'),
((SELECT id FROM posts WHERE title='승원토건은 천천히 쌓는 맛이 있네요' LIMIT 1), (SELECT id FROM users WHERE username='user101'), '기초공사 튼튼하면 좋죠. 제 멘탈도 철근 보강이 필요합니다.');
