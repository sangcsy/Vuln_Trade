import os
import time

from flask import current_app


def save_upload(upload):
    if not upload or not upload.filename:
        return None

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
