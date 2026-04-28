import hashlib
import random
from datetime import datetime, timedelta

import pymysql
from flask import current_app, g


ADMIN_USERNAME = "vuln@admin"
ADMIN_PASSWORD_HASH = "5206b8b8a996cf5320cb12ca91c7b790fba9f030408efe83ebb83548dc3007bd"
MOCK_USER_COUNT = 200
VIP_MOCK_USER_INDEX = 162
VIP_MOCK_BALANCE = 45_600_000_000


def _mock_password_hash(index):
    raw_password = f"VulnTrade!{index}#{index:03d}"
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def _mock_balance(index):
    if index == VIP_MOCK_USER_INDEX:
        return VIP_MOCK_BALANCE
    return 800_000 + (index * 15_700)


def _ensure_mock_users(cursor):
    for index in range(1, MOCK_USER_COUNT + 1):
        username = f"user{index}"
        display_name = f"모의투자자{index:03d}"
        cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                """
                UPDATE users
                SET password=%s, display_name=%s, balance=%s, role='user'
                WHERE username=%s
                """,
                (_mock_password_hash(index), display_name, _mock_balance(index), username),
            )
        else:
            cursor.execute(
                """
                INSERT INTO users (username, password, display_name, balance, role)
                VALUES (%s, %s, %s, %s, 'user')
                """,
                (username, _mock_password_hash(index), display_name, _mock_balance(index)),
            )


def _seed_vip_transfer_history(cursor):
    transfer_specs = [
        ("user162", "transfer_out", "user17", 300_000_000, "프라임 블록딜 정산", 11),
        ("user17", "transfer_in", "user162", 300_000_000, "프라임 블록딜 정산 수신", 11),
        ("user43", "transfer_out", "user162", 120_000_000, "장외 매각 대금", 24),
        ("user162", "transfer_in", "user43", 120_000_000, "장외 매각 대금 수신", 24),
        ("user162", "transfer_out", "user77", 250_000_000, "고액 담보 이체", 37),
        ("user77", "transfer_in", "user162", 250_000_000, "고액 담보 이체 수신", 37),
        ("user120", "transfer_out", "user162", 180_000_000, "투자금 회수", 52),
        ("user162", "transfer_in", "user120", 180_000_000, "투자금 회수 수신", 52),
        ("user162", "transfer_out", "user138", 100_000_000, "단기 운용금 이동", 68),
        ("user138", "transfer_in", "user162", 100_000_000, "단기 운용금 이동 수신", 68),
        ("user162", "transfer_out", "user195", 275_000_000, "기관 계좌 정산", 83),
        ("user195", "transfer_in", "user162", 275_000_000, "기관 계좌 정산 수신", 83),
    ]

    cursor.execute("SELECT id FROM transactions WHERE note=%s LIMIT 1", ("프라임 블록딜 정산",))
    if cursor.fetchone():
        return

    usernames = sorted({spec[0] for spec in transfer_specs} | {spec[2] for spec in transfer_specs})
    placeholders = ", ".join(["%s"] * len(usernames))
    cursor.execute(f"SELECT id, username FROM users WHERE username IN ({placeholders})", usernames)
    user_ids = {row["username"]: row["id"] for row in cursor.fetchall()}

    rows = []
    for actor, tx_type, target, amount, note, minutes_ago in transfer_specs:
        if actor not in user_ids or target not in user_ids:
            continue
        rows.append(
            (
                user_ids[actor],
                tx_type,
                amount,
                user_ids[target],
                note,
                datetime.now() - timedelta(minutes=minutes_ago),
            )
        )

    if rows:
        cursor.executemany(
            """
            INSERT INTO transactions (user_id, type, stock_id, quantity, amount, target_user_id, note, created_at)
            VALUES (%s, %s, NULL, NULL, %s, %s, %s, %s)
            """,
            rows,
        )


def _connect_from_config(config):
    return pymysql.connect(
        host=config["DB_HOST"],
        port=config["DB_PORT"],
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        database=config["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        charset="utf8mb4",
    )


def get_db():
    if "db" not in g:
        g.db = _connect_from_config(current_app.config)
    return g.db


def close_db(_=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _table_exists(cursor, table_name):
    cursor.execute("SHOW TABLES LIKE %s", (table_name,))
    return cursor.fetchone() is not None


def initialize_runtime_schema(app):
    db = _connect_from_config(app.config)
    try:
        with db.cursor() as cursor:
            if not _table_exists(cursor, "stocks") or not _table_exists(cursor, "users"):
                db.rollback()
                return

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS stock_price_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    stock_id INT NOT NULL,
                    current_price INT NOT NULL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_stock_recorded (stock_id, recorded_at),
                    CONSTRAINT fk_price_history_stock
                        FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )

            stocks_seed = [
                ("사성전자", "SSJ", 81200),
                ("SK로우닉스", "SKL", 163500),
                ("현소차", "HSC", 214000),
                ("현재오토네버", "HAN", 178400),
                ("퀴아", "KIA", 126500),
                ("두화", "DWH", 48700),
                ("너희은행", "NHB", 16200),
                ("둘은행", "DBK", 9580),
                ("제이뱅크", "JBK", 22400),
                ("인민은행", "PMB", 13150),
                ("태훈테크", "THT", 54800),
                ("수진바이오", "SJB", 38200),
                ("은결홀딩스", "EGH", 67400),
                ("희윤증권", "HYC", 29400),
                ("성준건설", "SJC", 42150),
                ("대한모터스", "DHM", 58700),
                ("한결바이오", "HGB", 44200),
                ("네오핀테크", "NEO", 73100),
                ('경석네트워크', 'KSN', 95000),
                ('민성게임즈', 'MSG', 68000),
                ('승원토건', 'SWC', 42000),
                ('슬로우푸드', 'SLF', 31000),
            ]
            for name, symbol, price in stocks_seed:
                cursor.execute("SELECT id FROM stocks WHERE symbol=%s", (symbol,))
                existing = cursor.fetchone()
                if existing:
                    cursor.execute(
                        "UPDATE stocks SET name=%s, current_price=%s WHERE symbol=%s",
                        (name, price, symbol),
                    )
                else:
                    cursor.execute(
                        "INSERT INTO stocks (name, symbol, current_price) VALUES (%s, %s, %s)",
                        (name, symbol, price),
                    )

            _ensure_mock_users(cursor)
            _seed_vip_transfer_history(cursor)

            users_seed = [
                (1, "총괄관리자"),
            ]
            for user_id, display_name in users_seed:
                cursor.execute("UPDATE users SET display_name=%s WHERE id=%s", (display_name, user_id))
            cursor.execute(
                "UPDATE users SET username=%s, password=%s WHERE id=1",
                (ADMIN_USERNAME, ADMIN_PASSWORD_HASH),
            )

            posts_seed = [
                (
                    1,
                    "사성전자 지금 들어가도 될까요?",
                    "실적 기대감이 다시 붙는 것 같아요. 단기 눌림에서 잡아도 괜찮을지 궁금합니다.",
                ),
                (
                    2,
                    "SK로우닉스 변동성 꽤 크네요",
                    "오늘 흐름은 강한데 눌림도 커서 진입 타이밍이 어렵네요.",
                ),
                (
                    3,
                    "모의투자 서비스 안내",
                    "실습 환경 특성상 시세는 외부 API가 아니라 내부 스케줄러 기준으로 움직입니다.",
                ),
            ]
            for post_id, title, content in posts_seed:
                cursor.execute("UPDATE posts SET title=%s, content=%s WHERE id=%s", (title, content, post_id))

            comments_seed = [
                (1, "저는 분할로 접근하는 쪽이 더 좋아 보여요."),
                (2, "오늘은 거래대금이 확실히 붙는 편입니다."),
                (3, "확인했습니다. 장 시작 전에 주문을 정리할게요."),
            ]
            for comment_id, content in comments_seed:
                cursor.execute("UPDATE comments SET content=%s WHERE id=%s", (content, comment_id))

            cursor.execute("SELECT id, current_price FROM stocks ORDER BY id")
            stocks = cursor.fetchall()
            for stock in stocks:
                cursor.execute(
                    "SELECT COUNT(*) AS cnt FROM stock_price_history WHERE stock_id=%s",
                    (stock["id"],),
                )
                count = cursor.fetchone()["cnt"]
                missing_points = max(0, 360 - count)
                if not missing_points:
                    continue

                rolling = stock["current_price"]
                points = []
                for idx in range(missing_points, 0, -1):
                    change_rate = random.uniform(-0.018, 0.018)
                    rolling = max(100, int(rolling * (1 + change_rate)))
                    points.append(
                        (
                            stock["id"],
                            rolling,
                            datetime.now() - timedelta(seconds=idx * 10),
                        )
                    )

                cursor.executemany(
                    """
                    INSERT INTO stock_price_history (stock_id, current_price, recorded_at)
                    VALUES (%s, %s, %s)
                    """,
                    points,
                )
        db.commit()
    finally:
        db.close()
