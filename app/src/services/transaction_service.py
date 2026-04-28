def create_transaction(cursor, user_id, tx_type, stock_id, quantity, amount, target_user_id, note):
    cursor.execute(
        """
        INSERT INTO transactions (user_id, type, stock_id, quantity, amount, target_user_id, note)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (user_id, tx_type, stock_id, quantity, amount, target_user_id, note),
    )


MAX_TRANSFER_AMOUNT = 1_000_000_000


def transfer_balance(db, sender_id, target_user_id, amount, note):
    if not isinstance(amount, int) or amount <= 0:
        return False, "송금액을 확인해 주세요."
    if amount > MAX_TRANSFER_AMOUNT:
        return False, "송금 한도를 초과했습니다."
    if sender_id == target_user_id:
        return False, "본인에게는 송금할 수 없습니다."

    with db.cursor() as cursor:
        cursor.execute("SELECT id, balance FROM users WHERE id=%s FOR UPDATE", (sender_id,))
        sender = cursor.fetchone()
        if not sender:
            return False, "사용자를 찾을 수 없습니다."
        if sender["balance"] < amount:
            return False, "잔액이 부족합니다."

        cursor.execute("SELECT id FROM users WHERE id=%s FOR UPDATE", (target_user_id,))
        target = cursor.fetchone()
        if not target:
            return False, "대상 사용자가 없습니다."

        cursor.execute("UPDATE users SET balance = balance - %s WHERE id=%s", (amount, sender_id))
        cursor.execute("UPDATE users SET balance = balance + %s WHERE id=%s", (amount, target_user_id))
        create_transaction(cursor, sender_id, "transfer_out", None, None, amount, target_user_id, note or "송금")
        create_transaction(cursor, target_user_id, "transfer_in", None, None, amount, sender_id, note or "송금 수신")
    db.commit()
    return True, "송금이 완료되었습니다."
