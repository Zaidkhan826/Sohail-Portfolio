import os
import sqlite3
import requests
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ---------------- CONFIG ----------------
app.secret_key = os.getenv("SECRET_KEY", "editorportfolio123")

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

ALLOWED_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------- HOME ----------------
@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        message = request.form["message"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO messages (name, email, message) VALUES (?, ?, ?)",
            (name, email, message)
        )

        conn.commit()
        conn.close()

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, filename FROM videos")
    videos = cursor.fetchall()
    conn.close()

    return render_template("index.html", videos=videos, success=True)

# ---------------- LOGIN ----------------
@app.route("/sohail-admin-986", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if (
            username == os.getenv("ADMIN_USERNAME")
            and password == os.getenv("ADMIN_PASSWORD")
        ):
            session["admin"] = True
            return redirect(url_for("dashboard"))
        else:
            return "Invalid Username or Password"

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard", methods=["GET"])
def dashboard():

    if "admin" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    search = request.args.get("search", "")

    if search:
        cursor.execute(
            "SELECT id, title, filename FROM videos WHERE title LIKE ?",
            ('%' + search + '%',)
        )
    else:
        cursor.execute("SELECT id, title, filename FROM videos")

    videos = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM messages")
    total_messages = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        videos=videos,
        total_videos=len(videos),
        total_messages=total_messages,
        search=search
    )

# ---------------- UPLOAD ----------------
@app.route("/upload", methods=["GET", "POST"])
def upload():

    if "admin" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        title = request.form["title"]
        video = request.files["video"]

        if video and allowed_file(video.filename):

            filename = secure_filename(video.filename)
            video.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO videos (title, filename) VALUES (?, ?)",
                (title, filename)
            )

            conn.commit()
            conn.close()

            return "Video Uploaded Successfully!"

        return "Invalid file type"

    return render_template("upload.html")

# ---------------- DELETE VIDEO ----------------
@app.route("/delete/<int:id>")
def delete(id):

    if "admin" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT filename FROM videos WHERE id=?", (id,))
    video = cursor.fetchone()

    if video:
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], video[0])
        if os.path.exists(filepath):
            os.remove(filepath)

    cursor.execute("DELETE FROM videos WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))

# ---------------- EDIT ----------------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    if "admin" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "POST":

        title = request.form["title"]

        cursor.execute(
            "UPDATE videos SET title=? WHERE id=?",
            (title, id)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    cursor.execute("SELECT title FROM videos WHERE id=?", (id,))
    video = cursor.fetchone()

    conn.close()

    return render_template("edit.html", video=video)

# ---------------- MESSAGES ----------------
@app.route("/messages")
def messages():

    if "admin" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM messages")
    messages = cursor.fetchall()

    conn.close()

    return render_template("messages.html", messages=messages)

# ---------------- REPLY (SAFE + WORKING) ----------------
@app.route("/reply/<int:id>", methods=["GET", "POST"])
def reply(id):

    if "admin" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name, email, message FROM messages WHERE id=?",
        (id,)
    )

    message = cursor.fetchone()

    if not message:
        conn.close()
        return "Message not found", 404

    if request.method == "POST":

        reply_text = request.form["reply"]

        try:
            response = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {os.getenv('RESEND_API_KEY')}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": "onboarding@resend.dev",
                    "to": message[1],
                    "subject": "Reply from Sohail Portfolio",
                    "html": f"""
                        <p>Hello {message[0]},</p>
                        <p>{reply_text}</p>
                        <br>
                        <p>Regards,<br>Sohail</p>
                    """
                }
            )

            print("EMAIL STATUS:", response.status_code, response.text)

        except Exception as e:
            print("EMAIL ERROR:", e)

        conn.close()
        return redirect(url_for("messages"))

    conn.close()
    return render_template("reply.html", message=message)

# ---------------- DELETE MESSAGE ----------------
@app.route("/delete_message/<int:id>")
def delete_message(id):

    if "admin" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM messages WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("messages"))

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("home"))

# ---------------- ERROR HANDLER ----------------
@app.errorhandler(RequestEntityTooLarge)
def file_too_large(e):
    return "❌ File is too large. Maximum allowed size is 100 MB.", 413

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)