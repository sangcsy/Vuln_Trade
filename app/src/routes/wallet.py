from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..db import get_db
from ..services.transaction_service import transfer_balance
from ..utils.decorators import login_required


wallet_bp = Blueprint("wallet", __name__)


@wallet_bp.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT id, username, display_name FROM users WHERE id != %s ORDER BY id", (session["user_id"],))
        users = cursor.fetchall()
        cursor.execute("SELECT balance FROM users WHERE id=%s", (session["user_id"],))
        user_row = cursor.fetchone()
        cursor.execute(
            """
            SELECT t.*, u.display_name AS actor_name, tu.display_name AS target_name
            FROM transactions t
            LEFT JOIN users u ON u.id = t.user_id
            LEFT JOIN users tu ON tu.id = t.target_user_id
            WHERE t.user_id=%s OR t.target_user_id=%s
            ORDER BY t.created_at DESC
            LIMIT 8
            """,
            (session["user_id"], session["user_id"]),
        )
        transactions = cursor.fetchall()

    if request.method == "POST":
        target_user_id = int(request.form.get("target_user_id", "0") or 0)
        amount = int(float(request.form.get("amount", "0") or 0))
        note = request.form.get("note", "")

        ok, message = transfer_balance(db, session["user_id"], target_user_id, amount, note)
        flash(message, "success" if ok else "error")
        return redirect(url_for("wallet.transfer"))

    return render_template(
        "wallet/transfer.html",
        users=users,
        balance=user_row["balance"] if user_row else 0,
        transactions=transactions,
    )


@wallet_bp.route("/history")
@login_required
def history():
    user_id = request.args.get("user_id", session["user_id"])
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT t.*, u.display_name AS actor_name, tu.display_name AS target_name
            FROM transactions t
            LEFT JOIN users u ON u.id = t.user_id
            LEFT JOIN users tu ON tu.id = t.target_user_id
            WHERE t.user_id=%s OR t.target_user_id=%s
            ORDER BY t.created_at DESC
            """,
            (user_id, user_id),
        )
        transactions = cursor.fetchall()
    return render_template("wallet/history.html", transactions=transactions)
