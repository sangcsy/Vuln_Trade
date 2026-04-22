from flask import Blueprint, render_template, request

from ..db import get_db
from ..utils.decorators import login_required


admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
@login_required
def dashboard():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS cnt FROM users")
        users_count = cursor.fetchone()["cnt"]
        cursor.execute("SELECT COUNT(*) AS cnt FROM posts")
        posts_count = cursor.fetchone()["cnt"]
        cursor.execute("SELECT COUNT(*) AS cnt FROM transactions")
        tx_count = cursor.fetchone()["cnt"]
        cursor.execute("SELECT SUM(balance) AS total_balance FROM users")
        total_balance = cursor.fetchone()["total_balance"] or 0

    return render_template(
        "admin/dashboard.html",
        users_count=users_count,
        posts_count=posts_count,
        tx_count=tx_count,
        total_balance=total_balance,
    )


@admin_bp.route("/users")
@login_required
def users():
    q = request.args.get("q", "")
    db = get_db()
    with db.cursor() as cursor:
        if q:
            query = f"""
            SELECT id, username, display_name, balance, role, created_at
            FROM users
            WHERE username LIKE '%{q}%'
               OR display_name LIKE '%{q}%'
               OR role LIKE '%{q}%'
            ORDER BY id
            """
            cursor.execute(query)
        else:
            cursor.execute("SELECT id, username, display_name, balance, role, created_at FROM users ORDER BY id")
        users = cursor.fetchall()
    return render_template("admin/users.html", users=users, q=q)


@admin_bp.route("/transactions")
@login_required
def transactions():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT t.*, u.display_name AS actor_name, tu.display_name AS target_name, s.symbol
            FROM transactions t
            LEFT JOIN users u ON u.id = t.user_id
            LEFT JOIN users tu ON tu.id = t.target_user_id
            LEFT JOIN stocks s ON s.id = t.stock_id
            ORDER BY t.created_at DESC
            LIMIT 100
            """
        )
        transactions = cursor.fetchall()
    return render_template("admin/transactions.html", transactions=transactions)


@admin_bp.route("/posts")
@login_required
def posts():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT p.id, p.title, p.created_at, u.display_name
            FROM posts p
            JOIN users u ON u.id = p.user_id
            ORDER BY p.created_at DESC
            """
        )
        posts = cursor.fetchall()
    return render_template("admin/posts.html", posts=posts)
