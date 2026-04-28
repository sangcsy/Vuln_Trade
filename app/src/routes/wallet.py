from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..db import get_db
from ..services.transaction_service import transfer_balance
from ..utils.decorators import login_required


wallet_bp = Blueprint("wallet", __name__)

TRANSFER_TABS = {
    "all": ("전체", ("transfer_in", "transfer_out")),
    "in": ("입금", ("transfer_in",)),
    "out": ("출금", ("transfer_out",)),
}


def parse_positive_int(value):
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return 0
    return parsed if parsed > 0 else 0


def get_transfer_tab():
    tab = request.args.get("tab", "all")
    return tab if tab in TRANSFER_TABS else "all"


def decorate_transfer(tx, current_user_id):
    is_outgoing = tx["type"] == "transfer_out"
    tx["display_type"] = "출금" if is_outgoing else "입금"
    tx["direction_label"] = tx["display_type"]
    tx["direction_class"] = "outgoing" if is_outgoing else "incoming"
    tx["from_name"] = tx["sender_name"] or "-"
    tx["to_name"] = tx["receiver_name"] or "-"
    tx["is_mine_sender"] = is_outgoing or tx["sender_id"] == current_user_id
    tx["is_mine_receiver"] = (not is_outgoing) or tx["receiver_id"] == current_user_id
    return tx


@wallet_bp.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():
    active_tab = get_transfer_tab()
    tab_types = TRANSFER_TABS[active_tab][1]
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT id, display_name FROM users WHERE id != %s ORDER BY id", (session["user_id"],))
        users = cursor.fetchall()
        cursor.execute("SELECT balance FROM users WHERE id=%s", (session["user_id"],))
        user_row = cursor.fetchone()
        cursor.execute(
            """
            SELECT t.*,
                   sender.id AS sender_id,
                   sender.display_name AS sender_name,
                   receiver.id AS receiver_id,
                   receiver.display_name AS receiver_name
            FROM transactions t
            LEFT JOIN users sender ON sender.id = CASE
                WHEN t.type='transfer_out' THEN t.user_id
                WHEN t.type='transfer_in' THEN t.target_user_id
                ELSE NULL
            END
            LEFT JOIN users receiver ON receiver.id = CASE
                WHEN t.type='transfer_out' THEN t.target_user_id
                WHEN t.type='transfer_in' THEN t.user_id
                ELSE NULL
            END
            WHERE t.user_id=%s
              AND t.type IN %s
            ORDER BY t.created_at DESC
            LIMIT 8
            """,
            (session["user_id"], tab_types),
        )
        transactions = [decorate_transfer(tx, session["user_id"]) for tx in cursor.fetchall()]

    if request.method == "POST":
        target_user_id = parse_positive_int(request.form.get("target_user_id"))
        amount = parse_positive_int(request.form.get("amount"))
        note = request.form.get("note", "")

        ok, message = transfer_balance(db, session["user_id"], target_user_id, amount, note)
        flash(message, "success" if ok else "error")
        return redirect(url_for("wallet.transfer"))

    return render_template(
        "wallet/transfer.html",
        users=users,
        balance=user_row["balance"] if user_row else 0,
        transactions=transactions,
        transfer_tabs=TRANSFER_TABS,
        active_tab=active_tab,
    )


@wallet_bp.route("/history")
@login_required
def history():
    active_tab = get_transfer_tab()
    tab_types = TRANSFER_TABS[active_tab][1]
    user_id = request.args.get("user_id", session["user_id"])
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT t.*,
                   sender.id AS sender_id,
                   sender.display_name AS sender_name,
                   receiver.id AS receiver_id,
                   receiver.display_name AS receiver_name
            FROM transactions t
            LEFT JOIN users sender ON sender.id = CASE
                WHEN t.type='transfer_out' THEN t.user_id
                WHEN t.type='transfer_in' THEN t.target_user_id
                ELSE NULL
            END
            LEFT JOIN users receiver ON receiver.id = CASE
                WHEN t.type='transfer_out' THEN t.target_user_id
                WHEN t.type='transfer_in' THEN t.user_id
                ELSE NULL
            END
            WHERE t.user_id=%s
              AND t.type IN %s
            ORDER BY t.created_at DESC
            """,
            (user_id, tab_types),
        )
        transactions = [decorate_transfer(tx, session["user_id"]) for tx in cursor.fetchall()]
    return render_template(
        "wallet/history.html",
        transactions=transactions,
        transfer_tabs=TRANSFER_TABS,
        active_tab=active_tab,
        selected_user_id=user_id,
    )
