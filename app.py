import os
from dotenv import load_dotenv

load_dotenv()

import sqlite3
import resend
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename

app = Flask(__name__)

resend.api_key = os.getenv("RESEND_API_KEY")


app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME")

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
app.secret_key = os.getenv("SECRET_KEY", "editorportfolio123")

ALLOWED_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm"}
def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )

@app.route('/send', methods=['POST'])
def send():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']

    print(name, email, message)
    return "Message sent successfully!"

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

    total_videos = len(videos)

    cursor.execute("SELECT COUNT(*) FROM messages")
    total_messages = cursor.fetchone()[0]

    conn.close()

    return render_template(
    "dashboard.html",
    videos=videos,
    total_videos=total_videos,
    total_messages=total_messages,
    search=search
)

@app.route("/upload", methods=["GET", "POST"])
def upload():

    if "admin" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        title = request.form["title"]
        video = request.files["video"]
        
        if not allowed_file(video.filename):
            return "Only MP4, MOV, AVI, MKV, and WEBM files are allowed."

        if video:
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

    return render_template("upload.html")

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

    return redirect(url_for("dashboard", deleted="1"))

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

    cursor.execute(
        "SELECT title FROM videos WHERE id=?",
        (id,)
    )

    video = cursor.fetchone()

    conn.close()

    return render_template("edit.html", video=video)

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

        print("Reply received:", reply_text)

        conn.close()
        return redirect(url_for("messages"))

    conn.close()
    return render_template("reply.html", message=message)

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("home"))

from werkzeug.exceptions import RequestEntityTooLarge

@app.errorhandler(RequestEntityTooLarge)
def file_too_large(e):
    return "❌ File is too large. Maximum allowed size is 100 MB.", 413

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

if __name__ == "__main__":
    app.run(debug=True)