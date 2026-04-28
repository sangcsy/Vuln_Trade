from functools import wraps

from flask import flash, redirect, request, session, url_for


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            flash("로그인이 필요합니다.", "error")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session.get("role") != "admin" or not session.get("admin_authenticated"):
            flash("관리자 로그인이 필요합니다.", "error")
            return redirect(url_for("auth.admin_login", next=request.url))
        return view(*args, **kwargs)

    return wrapped_view
