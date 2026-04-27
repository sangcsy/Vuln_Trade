import os
import time

from flask import current_app

ALLOWED_EXTENSIONS = {"jpg", "png"}
BANNED_INTERMEDIATE_EXTENSIONS = {"asp", "aspx", "php", "jsp", "jspx", "cgi", "pl", "exe", "py", "sh"}


def save_upload(upload):
    if not upload or not upload.filename:
        return None

    lowered = upload.filename.lower().strip()
    parts = [part for part in lowered.split(".") if part]
    if len(parts) < 2 or parts[-1] not in ALLOWED_EXTENSIONS:
        return {"error": "jpg \ub610\ub294 png \ud30c\uc77c\ub9cc \uc5c5\ub85c\ub4dc\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4."}
    if any(part in BANNED_INTERMEDIATE_EXTENSIONS for part in parts[:-1]):
        return {"error": "\uc774\ubbf8\uc9c0 \ud30c\uc77c\ub9cc \uc5c5\ub85c\ub4dc\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4."}

    base_name = upload.filename.replace("\\", "_").replace("/", "_")
    stored_name = f"{int(time.time())}_{base_name}"
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, stored_name)
    upload.save(file_path)

    return {
        "original_name": upload.filename,
        "stored_name": stored_name,
        "file_path": f"/app/src/static/uploads/{stored_name}",
    }
