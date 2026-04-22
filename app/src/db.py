import random
from datetime import datetime, timedelta

import pymysql
from flask import current_app, g


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

            users_seed = [
                (1, "총괄관리자"),
                (2, "김민준"),
                (3, "박서윤"),
            ]
            for user_id, display_name in users_seed:
                cursor.execute("UPDATE users SET display_name=%s WHERE id=%s", (display_name, user_id))

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
                cursor.execute("SELECT COUNT(*) AS cnt FROM stock_price_history WHERE stock_id=%s", (stock["id"],))
                count = cursor.fetchone()["cnt"]
                if count:
                    continue

                rolling = stock["current_price"]
                points = []
                for idx in range(24):
                    change_rate = random.uniform(-0.03, 0.03)
                    rolling = max(100, int(rolling * (1 + change_rate)))
                    points.append(
                        (
                            stock["id"],
                            rolling,
                            datetime.now() - timedelta(minutes=(24 - idx) * 5),
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
