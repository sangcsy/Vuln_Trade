from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..db import get_db
from ..utils.auth import hash_password, verify_password
from ..utils.seed import DEFAULT_BALANCE


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        display_name = request.form.get("display_name", "").strip()

        if not username or not password or not display_name:
            flash("모든 필드를 입력해 주세요.", "error")
            return render_template("auth/register.html")

        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
            if cursor.fetchone():
                flash("이미 존재하는 사용자입니다.", "error")
                return render_template("auth/register.html")

            cursor.execute(
                """
                INSERT INTO users (username, password, display_name, balance, role)
                VALUES (%s, %s, %s, %s, 'user')
                """,
                (username, hash_password(password), display_name, DEFAULT_BALANCE),
            )
        db.commit()
        flash("회원가입이 완료되었습니다.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        db = get_db()
        with db.cursor() as cursor:
            query = f"SELECT * FROM users WHERE username = '{username}' LIMIT 1"
            cursor.execute(query)
            user = cursor.fetchone()

        if user and user["role"] == "admin" and verify_password(password, user["password"]):
            flash("관리자 계정은 관리자 로그인 페이지를 이용해 주세요.", "error")
            return render_template("auth/login.html")

        if user and verify_password(password, user["password"]):
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session.pop("admin_authenticated", None)
            flash("로그인되었습니다.", "success")
            return redirect(url_for("main.index"))

        flash("아이디 또는 비밀번호가 올바르지 않습니다.", "error")

    return render_template("auth/login.html")


@auth_bp.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    next_url = request.args.get("next") or request.form.get("next") or url_for("admin.dashboard")

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        db = get_db()
        with db.cursor() as cursor:
            query = f"SELECT * FROM users WHERE username = '{username}' LIMIT 1"
            cursor.execute(query)
            user = cursor.fetchone()

        if user and user["role"] == "admin" and verify_password(password, user["password"]):
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["admin_authenticated"] = True
            flash("관리자 인증이 완료되었습니다.", "success")
            return redirect(next_url)

        flash("관리자 자격증명이 올바르지 않습니다.", "error")

    return render_template("admin/login.html", next_url=next_url)


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("로그아웃되었습니다.", "success")
    return redirect(url_for("main.index"))
