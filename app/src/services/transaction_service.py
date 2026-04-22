def create_transaction(cursor, user_id, tx_type, stock_id, quantity, amount, target_user_id, note):
    cursor.execute(
        """
        INSERT INTO transactions (user_id, type, stock_id, quantity, amount, target_user_id, note)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (user_id, tx_type, stock_id, quantity, amount, target_user_id, note),
    )


def transfer_balance(db, sender_id, target_user_id, amount, note):
    with db.cursor() as cursor:
        cursor.execute("SELECT id FROM users WHERE id=%s", (target_user_id,))
        target = cursor.fetchone()
        if not target:
            return False, "대상 사용자가 없습니다."

        cursor.execute("UPDATE users SET balance = balance - %s WHERE id=%s", (amount, sender_id))
        cursor.execute("UPDATE users SET balance = balance + %s WHERE id=%s", (amount, target_user_id))
        create_transaction(cursor, sender_id, "transfer_out", None, None, amount, target_user_id, note or "송금")
        create_transaction(cursor, target_user_id, "transfer_in", None, None, amount, sender_id, note or "송금 수신")
    db.commit()
    return True, "송금이 완료되었습니다."
