import os

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app

from ..db import get_db
from ..services.file_service import save_upload
from ..utils.decorators import admin_required


admin_bp = Blueprint("admin", __name__)

TRANSACTION_TABS = {
    "all": ("전체", ("buy", "sell", "transfer_in", "transfer_out")),
    "buy": ("매수", ("buy",)),
    "sell": ("매도", ("sell",)),
    "in": ("입금", ("transfer_in",)),
    "out": ("출금", ("transfer_out",)),
}


def get_transaction_tab():
    tab = request.args.get("tab", "all")
    return tab if tab in TRANSACTION_TABS else "all"


@admin_bp.route("")
@admin_bp.route("/")
@admin_required
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
@admin_required
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
@admin_required
def transactions():
    active_tab = get_transaction_tab()
    tab_types = TRANSACTION_TABS[active_tab][1]
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT t.*, u.display_name AS actor_name, tu.display_name AS target_name, s.symbol
            FROM transactions t
            LEFT JOIN users u ON u.id = t.user_id
            LEFT JOIN users tu ON tu.id = t.target_user_id
            LEFT JOIN stocks s ON s.id = t.stock_id
            WHERE t.type IN %s
            ORDER BY t.created_at DESC
            LIMIT 100
            """,
            (tab_types,),
        )
        transactions = cursor.fetchall()
    return render_template(
        "admin/transactions.html",
        transactions=transactions,
        transaction_tabs=TRANSACTION_TABS,
        active_tab=active_tab,
    )


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_user(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT id, username, display_name, balance, role FROM users WHERE id=%s", (user_id,))
        user = cursor.fetchone()
    if not user:
        flash("사용자를 찾을 수 없습니다.", "error")
        return redirect(url_for("admin.users"))
    if request.method == "POST":
        display_name = request.form.get("display_name", "")
        with db.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET display_name=%s WHERE id=%s",
                (display_name, user_id),
            )
        db.commit()
        flash("사용자 정보가 수정되었습니다.", "success")
        return redirect(url_for("admin.users"))
    return render_template("admin/edit_user.html", user=user)


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
    db.commit()
    flash("사용자가 삭제되었습니다.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/posts")
@admin_required
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


@admin_bp.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_post(post_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM posts WHERE id=%s", (post_id,))
        post = cursor.fetchone()
    if not post:
        flash("게시글을 찾을 수 없습니다.", "error")
        return redirect(url_for("admin.posts"))
    if request.method == "POST":
        title = request.form.get("title", "")
        content = request.form.get("content", "")
        with db.cursor() as cursor:
            cursor.execute(
                "UPDATE posts SET title=%s, content=%s, updated_at=NOW() WHERE id=%s",
                (title, content, post_id),
            )
            upload = request.files.get("attachment")
            saved = save_upload(upload)
            if saved and saved.get("error"):
                db.rollback()
                flash(saved["error"], "error")
                cursor.execute("SELECT * FROM files WHERE post_id=%s ORDER BY created_at DESC", (post_id,))
                files = cursor.fetchall()
                return render_template("admin/edit_post.html", post=post, files=files)
            if saved:
                cursor.execute(
                    "INSERT INTO files (user_id, post_id, original_name, stored_name, file_path) VALUES (%s, %s, %s, %s, %s)",
                    (post["user_id"], post_id, saved["original_name"], saved["stored_name"], saved["file_path"]),
                )
        db.commit()
        flash("게시글이 수정되었습니다.", "success")
        return redirect(url_for("admin.edit_post", post_id=post_id))
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM files WHERE post_id=%s ORDER BY created_at DESC", (post_id,))
        files = cursor.fetchall()
    return render_template("admin/edit_post.html", post=post, files=files)


@admin_bp.route("/posts/<int:post_id>/files/<int:file_id>/delete", methods=["POST"])
@admin_required
def delete_post_file(post_id, file_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM files WHERE id=%s AND post_id=%s", (file_id, post_id))
        file_data = cursor.fetchone()
    if file_data:
        real_path = os.path.join(current_app.config["UPLOAD_FOLDER"], file_data["stored_name"])
        if os.path.exists(real_path):
            os.remove(real_path)
        with db.cursor() as cursor:
            cursor.execute("DELETE FROM files WHERE id=%s", (file_id,))
        db.commit()
    return redirect(url_for("admin.edit_post", post_id=post_id))


@admin_bp.route("/posts/<int:post_id>/delete", methods=["POST"])
@admin_required
def delete_post(post_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM posts WHERE id=%s", (post_id,))
    db.commit()
    flash("게시글이 삭제되었습니다.", "success")
    return redirect(url_for("admin.posts"))
