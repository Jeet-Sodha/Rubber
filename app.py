import os
from functools import wraps
from datetime import datetime

from flask import (
    Flask,
    request,
    redirect,
    url_for,
    session,
    send_from_directory,
    render_template,
    abort,
)
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "local-development-secret")

USERNAME = os.environ.get("PORTAL_USERNAME", "myuser")
PASSWORD = os.environ.get("PORTAL_PASSWORD", "mypassword")

STORAGE_DIR = os.environ.get("STORAGE_DIR", "storage")

os.makedirs(STORAGE_DIR, exist_ok=True)


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return func(*args, **kwargs)

    return wrapper


@app.route("/")
@login_required
def index():
    files = []

    for filename in os.listdir(STORAGE_DIR):
        path = os.path.join(STORAGE_DIR, filename)

        if os.path.isfile(path):
            size = os.path.getsize(path)
            modified = os.path.getmtime(path)

            files.append({
                "name": filename,
                "size": size,
                "timestamp": datetime.fromtimestamp(
                    modified
                ).strftime("%Y-%m-%d %H:%M:%S")
            })

    files.sort(key=lambda x: x["timestamp"], reverse=True)

    return render_template("files.html", files=files)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == USERNAME and password == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))

        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =========================
# UPLOAD
# =========================

@app.route("/api/upload", methods=["POST"])
def upload():
    uploaded = request.files.get("file")

    if not uploaded or not uploaded.filename:
        return "No file supplied", 400

    filename = secure_filename(uploaded.filename)

    if not filename:
        return "Invalid filename", 400

    # Create a serial number if filename already exists
    original_name = filename
    name, extension = os.path.splitext(original_name)

    counter = 0

    while os.path.exists(os.path.join(STORAGE_DIR, filename)):
        counter += 1
        filename = f"{name}_{counter}{extension}"

    path = os.path.join(STORAGE_DIR, filename)

    uploaded.save(path)

    return f"Upload successful: {filename}", 200


# =========================
# DOWNLOAD
# =========================

@app.route("/download/<filename>")
@login_required
def download(filename):
    filename = secure_filename(filename)

    if not filename:
        abort(404)

    path = os.path.join(STORAGE_DIR, filename)

    if not os.path.exists(path):
        abort(404)

    return send_from_directory(
        STORAGE_DIR,
        filename,
        as_attachment=True
    )


# =========================
# DELETE ONE FILE
# =========================

@app.route("/delete/<filename>", methods=["POST"])
@login_required
def delete_file(filename):
    filename = secure_filename(filename)

    if not filename:
        abort(404)

    path = os.path.join(STORAGE_DIR, filename)

    if os.path.exists(path):
        os.remove(path)

    return redirect(url_for("index"))


# =========================
# DELETE ALL FILES
# =========================

@app.route("/delete-all", methods=["POST"])
@login_required
def delete_all():
    for filename in os.listdir(STORAGE_DIR):
        path = os.path.join(STORAGE_DIR, filename)

        if os.path.isfile(path):
            os.remove(path)

    return redirect(url_for("index"))


@app.route("/health")
def health():
    return "OK"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)