import os
import random
import time

import pymysql


def connect():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "db"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "vulntrade"),
        password=os.getenv("MYSQL_PASSWORD", "vulntrade123"),
        database=os.getenv("MYSQL_DATABASE", "vulntrade"),
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
        charset="utf8mb4",
    )


def ensure_history_table(cursor):
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


def update_prices():
    db = connect()
    with db.cursor() as cursor:
        ensure_history_table(cursor)
        cursor.execute("SELECT id, current_price, initial_price FROM stocks")
        stocks = cursor.fetchall()
        for stock in stocks:
            rate = random.uniform(-0.05, 0.05)
            if stock["current_price"] < stock["initial_price"]:
                pull = (stock["initial_price"] - stock["current_price"]) / stock["initial_price"] * 0.02
                rate += pull
            new_price = max(100, int(stock["current_price"] * (1 + rate)))
            cursor.execute(
                "UPDATE stocks SET current_price=%s, updated_at=NOW() WHERE id=%s",
                (new_price, stock["id"]),
            )
            cursor.execute(
                "INSERT INTO stock_price_history (stock_id, current_price) VALUES (%s, %s)",
                (stock["id"], new_price),
            )
            cursor.execute(
                """
                DELETE FROM stock_price_history
                WHERE stock_id=%s
                  AND id NOT IN (
                      SELECT id FROM (
                          SELECT id
                          FROM stock_price_history
                          WHERE stock_id=%s
                          ORDER BY recorded_at DESC
                          LIMIT 10000
                      ) AS recent_rows
                  )
                """,
                (stock["id"], stock["id"]),
            )
    db.close()


if __name__ == "__main__":
    interval = int(os.getenv("PRICE_UPDATE_INTERVAL", "1"))
    while True:
        try:
            update_prices()
        except Exception:
            pass
        time.sleep(interval)
