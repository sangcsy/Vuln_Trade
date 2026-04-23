import os
import time

from flask import current_app

ALLOWED_EXTENSIONS = {"jpg", "png"}
BANNED_INTERMEDIATE_EXTENSIONS = {"asp", "aspx", "php", "jsp", "jspx", "cgi", "pl", "exe", "py", "sh"}
JPEG_MAGIC = b"\xff\xd8\xff"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def looks_like_allowed_image(upload, extension):
    header = upload.stream.read(16)
    upload.stream.seek(0)

    if extension == "jpg":
        return header.startswith(JPEG_MAGIC)
    if extension == "png":
        return header.startswith(PNG_MAGIC)
    return False


def save_upload(upload):
    if not upload or not upload.filename:
        return None

    lowered = upload.filename.lower().strip()
    parts = [part for part in lowered.split(".") if part]
    if len(parts) < 2 or parts[-1] not in ALLOWED_EXTENSIONS:
        return {"error": "jpg 또는 png 파일만 업로드할 수 있습니다."}
    if any(part in BANNED_INTERMEDIATE_EXTENSIONS for part in parts[:-1]):
        return {"error": "이미지 파일만 업로드할 수 있습니다."}
    if not looks_like_allowed_image(upload, parts[-1]):
        return {"error": "이미지 형식이 올바르지 않습니다."}

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
