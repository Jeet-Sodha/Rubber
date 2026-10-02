import os
from functools import wraps

from flask import (
    Flask,
    request,
    redirect,
    url_for,
    session,
    send_file,
    render_template,
    abort,
)

app = Flask(__name__)

# =========================
# CONFIGURATION
# =========================

app.secret_key = os.environ.get("SECRET_KEY", "local-development-secret")

USERNAME = os.environ.get("PORTAL_USERNAME", "myuser")
PASSWORD = os.environ.get("PORTAL_PASSWORD", "mypassword")

STORAGE_DIR = os.environ.get("STORAGE_DIR", "storage")

os.makedirs(STORAGE_DIR, exist_ok=True)


# =========================
# LOGIN PROTECTION
# =========================

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))

        return func(*args, **kwargs)

    return wrapper


# =========================
# WEBSITE
# =========================

@app.route("/")
@login_required
def index():

    files = []

    for filename in os.listdir(STORAGE_DIR):

        filepath = os.path.join(STORAGE_DIR, filename)

        if os.path.isfile(filepath):
            files.append({
                "name": filename,
                "size": os.path.getsize(filepath)
            })

    return render_template(
        "files.html",
        files=files
    )


# =========================
# LOGIN
# =========================

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


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================
# PUBLIC CMD UPLOAD
# =========================

@app.route("/api/upload", methods=["POST"])
def api_upload():

    uploaded = request.files.get("file")

    if not uploaded or not uploaded.filename:
        return "No file supplied", 400

    # Only allow ZIP files
    if not uploaded.filename.lower().endswith(".zip"):
        return "Only ZIP files are allowed", 400

    # Always save using a fixed filename
    # so uploaded ZIP replaces the previous one.
    filepath = os.path.join(
        STORAGE_DIR,
        "downloads_last_30_days.zip"
    )

    uploaded.save(filepath)

    return "Upload successful", 200


# =========================
# PRIVATE BROWSER DOWNLOAD
# =========================

@app.route("/download/<filename>")
@login_required
def download(filename):

    filepath = os.path.join(
        STORAGE_DIR,
        filename
    )

    if not os.path.isfile(filepath):
        abort(404)

    return send_file(
        filepath,
        as_attachment=True,
        download_name=filename
    )


# =========================
# HEALTH CHECK
# =========================

@app.route("/health")
def health():

    return "OK"


# =========================
# START SERVER
# =========================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )