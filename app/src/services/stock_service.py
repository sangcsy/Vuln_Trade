from .transaction_service import create_transaction


def buy_stock(db, user_id, stock, quantity, total_price):
    with db.cursor() as cursor:
        cursor.execute("SELECT balance FROM users WHERE id=%s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return False, "사용자를 찾을 수 없습니다."

        if user["balance"] < total_price:
            return False, "잔액이 부족합니다."

        cursor.execute(
            "SELECT * FROM holdings WHERE user_id=%s AND stock_id=%s",
            (user_id, stock["id"]),
        )
        holding = cursor.fetchone()

        if holding:
            new_quantity = holding["quantity"] + quantity
            new_avg = int(((holding["avg_price"] * holding["quantity"]) + total_price) / max(new_quantity, 1))
            cursor.execute(
                "UPDATE holdings SET quantity=%s, avg_price=%s WHERE id=%s",
                (new_quantity, new_avg, holding["id"]),
            )
        else:
            cursor.execute(
                "INSERT INTO holdings (user_id, stock_id, quantity, avg_price) VALUES (%s, %s, %s, %s)",
                (user_id, stock["id"], quantity, int(total_price / max(quantity, 1))),
            )

        cursor.execute("UPDATE users SET balance = balance - %s WHERE id=%s", (total_price, user_id))
        create_transaction(cursor, user_id, "buy", stock["id"], quantity, total_price, None, f"{stock['symbol']} 매수")
    db.commit()
    return True, "매수가 완료되었습니다."


def sell_stock(db, user_id, stock, quantity, total_price):
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM holdings WHERE user_id=%s AND stock_id=%s",
            (user_id, stock["id"]),
        )
        holding = cursor.fetchone()
        if not holding or holding["quantity"] < quantity:
            return False, "보유 수량이 부족합니다."

        remaining = holding["quantity"] - quantity
        if remaining == 0:
            cursor.execute("DELETE FROM holdings WHERE id=%s", (holding["id"],))
        else:
            cursor.execute("UPDATE holdings SET quantity=%s WHERE id=%s", (remaining, holding["id"]))

        cursor.execute("UPDATE users SET balance = balance + %s WHERE id=%s", (total_price, user_id))
        create_transaction(cursor, user_id, "sell", stock["id"], quantity, total_price, None, f"{stock['symbol']} 매도")
    db.commit()
    return True, "매도가 완료되었습니다."
