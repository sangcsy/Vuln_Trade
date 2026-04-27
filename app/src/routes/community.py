import os

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_file, session, url_for

from ..db import get_db
from ..services.file_service import save_upload
from ..utils.decorators import login_required


community_bp = Blueprint("community", __name__)


@community_bp.route("/")
def list_posts():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT p.id, p.title, p.content, p.created_at, p.updated_at, u.display_name
            FROM posts p
            JOIN users u ON u.id = p.user_id
            ORDER BY p.created_at DESC
            """
        )
        posts = cursor.fetchall()
    return render_template("community/list.html", posts=posts)


@community_bp.route("/<int:post_id>")
def detail(post_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT p.*, u.display_name
            FROM posts p
            JOIN users u ON u.id = p.user_id
            WHERE p.id=%s
            """,
            (post_id,),
        )
        post = cursor.fetchone()
        cursor.execute(
            """
            SELECT c.*, u.display_name
            FROM comments c
            JOIN users u ON u.id = c.user_id
            WHERE c.post_id=%s
            ORDER BY c.created_at ASC
            """,
            (post_id,),
        )
        comments = cursor.fetchall()
        cursor.execute("SELECT * FROM files WHERE post_id=%s ORDER BY created_at DESC", (post_id,))
        files = cursor.fetchall()

    if not post:
        flash("Post not found.", "error")
        return redirect(url_for("community.list_posts"))

    return render_template("community/detail.html", post=post, comments=comments, files=files)


@community_bp.route("/write", methods=["GET", "POST"])
@login_required
def write():
    if request.method == "POST":
        title = request.form.get("title", "")
        content = request.form.get("content", "")

        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO posts (user_id, title, content) VALUES (%s, %s, %s)",
                (session["user_id"], title, content),
            )
            post_id = cursor.lastrowid

            upload = request.files.get("attachment")
            saved = save_upload(upload)
            if saved and saved.get("error"):
                db.rollback()
                flash(saved["error"], "error")
                return render_template("community/write.html", title=title, content=content)
            if saved:
                cursor.execute(
                    """
                    INSERT INTO files (user_id, post_id, original_name, stored_name, file_path)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        session["user_id"],
                        post_id,
                        saved["original_name"],
                        saved["stored_name"],
                        saved["file_path"],
                    ),
                )
        db.commit()
        flash("Post created.", "success")
        return redirect(url_for("community.detail", post_id=post_id))

    return render_template("community/write.html")


@community_bp.route("/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit(post_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM posts WHERE id=%s", (post_id,))
        post = cursor.fetchone()

    if not post:
        flash("Post not found.", "error")
        return redirect(url_for("community.list_posts"))

    if post["user_id"] != session.get("user_id"):
        flash("You can only edit your own posts.", "error")
        return redirect(url_for("community.detail", post_id=post_id))

    if request.method == "POST":
        title = request.form.get("title", "")
        content = request.form.get("content", "")
        with db.cursor() as cursor:
            cursor.execute(
                "UPDATE posts SET title=%s, content=%s, updated_at=NOW() WHERE id=%s",
                (title, content, post_id),
            )
        db.commit()
        flash("Post updated.", "success")
        return redirect(url_for("community.detail", post_id=post_id))

    return render_template("community/edit.html", post=post)


@community_bp.route("/<int:post_id>/delete", methods=["POST"])
@login_required
def delete(post_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM posts WHERE id=%s", (post_id,))
    db.commit()
    flash("Post deleted.", "success")
    return redirect(url_for("community.list_posts"))


@community_bp.route("/<int:post_id>/comment", methods=["POST"])
@login_required
def write_comment(post_id):
    content = request.form.get("content", "")
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO comments (post_id, user_id, content) VALUES (%s, %s, %s)",
            (post_id, session["user_id"], content),
        )
    db.commit()
    return redirect(url_for("community.detail", post_id=post_id))


@community_bp.route("/file")
@login_required
def download():
    filename = request.args.get("name")
    if not filename:
        flash("File not found.", "error")
        return redirect(url_for("community.list_posts"))

    real_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(real_path):
        flash("File not found.", "error")
        return redirect(url_for("community.list_posts"))

    return send_file(real_path, as_attachment=True, download_name=os.path.basename(filename))
