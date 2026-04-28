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
    if index == VIP_MOCK_USER_INDEX:
        return "65c21921ca10a8502757efc9aa552874d181c6206feb2845a921eb57f5e518d4"
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


MOCK_COMMUNITY_POSTS = [
    (
        "user20",
        "성준건설 차트가 삽질하다가 유전 찾은 모양입니다",
        "분명 아침에는 지하실로 가는 줄 알았는데 오후에 갑자기 양봉을 세웠네요. 제 계좌도 같이 굴착 중입니다.",
    ),
    (
        "user37",
        "네오핀테크 매수 버튼 누르기 전 손가락 회의 결과",
        "엄지와 검지는 찬성, 이성은 반대했습니다. 일단 1주만 사고 제 마음의 변동성을 관찰해보겠습니다.",
    ),
    (
        "user58",
        "둘은행은 이름처럼 둘 중 하나만 해줬으면 좋겠습니다",
        "오르거나 내리거나 둘 중 하나인데 왜 제 평단만 정확히 피해 가는지 모르겠습니다.",
    ),
    (
        "user74",
        "사성전자 주주총회 대신 제 통장총회 열었습니다",
        "안건은 물타기 승인 여부였고 참석자 1명 만장일치로 보류됐습니다. 라면 예산이 더 중요합니다.",
    ),
    (
        "user91",
        "SK로우닉스 변동성 보고 커피 두 잔 마셨습니다",
        "차트가 이미 카페인 과다 섭취 상태라 저는 디카페인으로 갈아탔습니다. 그래도 눈은 못 떼겠네요.",
    ),
    (
        "user118",
        "인민은행 배당 기대감으로 계산기 두드렸습니다",
        "계산 결과 배당보다 제가 어제 시킨 치킨값이 더 컸습니다. 장기투자의 길은 멀고 양념은 가까웠습니다.",
    ),
    (
        "user136",
        "현소차 오늘 주행감 좋네요",
        "제 계좌는 아직 사이드브레이크가 잠겨 있는데 종목은 고속도로를 탄 것 같습니다. 탑승 타이밍이 문제네요.",
    ),
    (
        "user149",
        "태훈테크 단타 치려다가 장투 선언했습니다",
        "매도 타이밍을 놓친 것이 아니라 투자 철학이 갑자기 깊어진 것입니다. 아무튼 그렇습니다.",
    ),
    (
        "user177",
        "희윤증권 리포트 읽다가 제 잔고 리포트도 봤습니다",
        "투자의견은 매수인데 제 잔고 의견은 휴식입니다. 시장보다 월급날이 더 기다려집니다.",
    ),
    (
        "user194",
        "슬로우푸드 이름값 제대로 하네요",
        "상승도 슬로우, 체결도 슬로우, 제 인내심만 패스트로 소진 중입니다. 그래도 컨셉은 확실합니다.",
    ),
    (
        "user162",
        "호가창에 0이 많으면 마음도 무거워지네요",
        "분산투자 연습한다고 몇 종목 눌러봤는데 주문 확인 버튼 앞에서는 아직도 손이 떨립니다. 이상하게 1주씩 사는 연습보다 이체 메모 정리가 더 오래 걸리네요.",
    ),
]


def _ensure_mock_posts(cursor):
    for username, title, content in MOCK_COMMUNITY_POSTS:
        cursor.execute("SELECT id FROM posts WHERE title=%s LIMIT 1", (title,))
        if cursor.fetchone():
            continue
        cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        if not user:
            continue
        cursor.execute(
            "INSERT INTO posts (user_id, title, content) VALUES (%s, %s, %s)",
            (user["id"], title, content),
        )


MOCK_COMMUNITY_COMMENTS = [
    ("사성전자 지금 들어가도 될까요?", "user22", "저는 들어가기 전에 항상 커피부터 삽니다. 손 떨림 방지용입니다."),
    ("사성전자 지금 들어가도 될까요?", "user81", "분할 매수면 마음은 편한데 잔고가 분할되는 기분도 같이 옵니다."),
    ("SK로우닉스 변동성 꽤 크네요", "user44", "이 정도 흔들림이면 차트가 아니라 놀이기구 이용권입니다."),
    ("모의투자 서비스 안내", "user13", "실시간처럼 움직여서 제 심장도 실시간으로 반응 중입니다."),
    ("성준건설 차트가 삽질하다가 유전 찾은 모양입니다", "user63", "저도 굴착 들어갔다가 제 평단만 매장되는 중입니다."),
    ("성준건설 차트가 삽질하다가 유전 찾은 모양입니다", "user142", "유전이면 좋겠는데 제 계좌에서는 아직 흙냄새만 납니다."),
    ("네오핀테크 매수 버튼 누르기 전 손가락 회의 결과", "user28", "제 손가락 회의는 늘 매수 찬성인데 회계팀이 반대합니다."),
    ("둘은행은 이름처럼 둘 중 하나만 해줬으면 좋겠습니다", "user105", "오르지도 내리지도 않으면 제 감정만 상장폐지됩니다."),
    ("둘은행은 이름처럼 둘 중 하나만 해줬으면 좋겠습니다", "user188", "둘 중 하나라더니 제 선택지만 늘 틀리는 게 문제네요."),
    ("사성전자 주주총회 대신 제 통장총회 열었습니다", "user34", "라면 예산은 중대 사안이라 의결권 행사 신중해야 합니다."),
    ("SK로우닉스 변동성 보고 커피 두 잔 마셨습니다", "user156", "저는 차트 보고 디카페인 마셨는데도 손이 떨립니다."),
    ("인민은행 배당 기대감으로 계산기 두드렸습니다", "user72", "치킨 수익률은 언제나 확정 수익이라 강합니다."),
    ("현소차 오늘 주행감 좋네요", "user130", "저는 아직 정류장에 있는데 종목은 톨게이트 지난 것 같습니다."),
    ("현소차 오늘 주행감 좋네요", "user19", "탑승하려고 하면 꼭 급정거해서 안전벨트만 꽉 잡습니다."),
    ("태훈테크 단타 치려다가 장투 선언했습니다", "user51", "장투 선언은 보통 손절 버튼을 못 봤을 때 나옵니다."),
    ("희윤증권 리포트 읽다가 제 잔고 리포트도 봤습니다", "user99", "제 잔고 리포트 투자의견은 관망입니다. 아주 장기 관망입니다."),
    ("슬로우푸드 이름값 제대로 하네요", "user168", "느린 건 좋은데 제 인내심만 초단타로 빠져나갑니다."),
    ("슬로우푸드 이름값 제대로 하네요", "user7", "이름값 확실하네요. 수익도 천천히 오면 좋겠습니다."),
    ("호가창에 0이 많으면 마음도 무거워지네요", "user48", "0이 많을수록 손가락이 공손해지는 효과가 있습니다."),
    ("호가창에 0이 많으면 마음도 무거워지네요", "user162", "그래서 저는 메모를 꼼꼼히 씁니다. 나중에 제가 봐도 헷갈리더라고요."),
]


def _ensure_mock_comments(cursor):
    for post_title, username, content in MOCK_COMMUNITY_COMMENTS:
        cursor.execute("SELECT id FROM posts WHERE title=%s LIMIT 1", (post_title,))
        post = cursor.fetchone()
        cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        if not post or not user:
            continue
        cursor.execute(
            "SELECT id FROM comments WHERE post_id=%s AND content=%s LIMIT 1",
            (post["id"], content),
        )
        if cursor.fetchone():
            continue
        cursor.execute(
            "INSERT INTO comments (post_id, user_id, content) VALUES (%s, %s, %s)",
            (post["id"], user["id"], content),
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
            _ensure_mock_posts(cursor)

            comments_seed = [
                (1, "저는 분할로 접근하는 쪽이 더 좋아 보여요."),
                (2, "오늘은 거래대금이 확실히 붙는 편입니다."),
                (3, "확인했습니다. 장 시작 전에 주문을 정리할게요."),
            ]
            for comment_id, content in comments_seed:
                cursor.execute("UPDATE comments SET content=%s WHERE id=%s", (content, comment_id))
            _ensure_mock_comments(cursor)

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
