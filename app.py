import os
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple
from urllib.parse import urlparse

from flask import Flask, flash, redirect, render_template, request, url_for

UPLOAD_DIR = Path(tempfile.gettempdir()) / "web_printer_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "bmp",
    "tiff",
    "txt",
    "doc",
    "docx",
    "ppt",
    "pptx",
    "xls",
    "xlsx",
}


def allowed_file(filename: str) -> bool:
    if not filename:
        return False
    if "." not in filename:
        return True
    return filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def normalize_printer_target(raw_value: str) -> str:
    value = (raw_value or "").strip()
    if not value:
        return ""
    value = value.replace(" ", "")
    if value.startswith(("ipp://", "ipps://", "socket://", "lpd://")):
        return value
    return f"ipp://{value}/ipp/print"


def send_via_lp(printer_uri: str, file_path: Path) -> Tuple[bool, str]:
    if not shutil.which("lp"):
        return False, "The 'lp' command is not available on this system. Install CUPS to enable IPP printing."

    cmd = ["lp", "-d", printer_uri, str(file_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, result.stderr.strip() or "Failed to submit the print job via lp."
    return True, result.stdout.strip() or "Print job submitted successfully."


def send_via_socket(printer_uri: str, file_path: Path) -> Tuple[bool, str]:
    parsed = urlparse(printer_uri)
    if not parsed.hostname:
        return False, "Unable to determine printer hostname from the provided address."
    port = parsed.port or 9100
    try:
        with socket.create_connection((parsed.hostname, port), timeout=10) as sock, file_path.open("rb") as handle:
            while True:
                chunk = handle.read(8192)
                if not chunk:
                    break
                sock.sendall(chunk)
    except OSError as exc:
        return False, f"Failed to send data to printer: {exc}"
    return True, "Print job sent to printer over raw socket successfully."


def dispatch_print_job(printer_input: str, file_path: Path) -> Tuple[bool, str]:
    printer_uri = normalize_printer_target(printer_input)
    if not printer_uri:
        return False, "Please provide a printer address."

    parsed = urlparse(printer_uri)
    scheme = parsed.scheme.lower()

    if scheme in {"ipp", "ipps", "lpd"}:
        return send_via_lp(printer_uri, file_path)
    if scheme == "socket":
        return send_via_socket(printer_uri, file_path)

    return False, "Unsupported printer protocol. Use ipp(s)://, socket://, or provide an IP address."


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024  # 64 MiB


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        printer_address = request.form.get("printer_address", "")
        uploaded_file = request.files.get("document")

        if not uploaded_file or uploaded_file.filename == "":
            flash("Please choose a file to print.", "error")
            return redirect(url_for("index"))

        if not allowed_file(uploaded_file.filename):
            flash("Unsupported file type. Please upload a standard document or image format.", "error")
            return redirect(url_for("index"))

        with tempfile.NamedTemporaryFile(dir=UPLOAD_DIR, delete=False) as temp_file:
            uploaded_file.save(temp_file)
            temp_path = Path(temp_file.name)

        success, message = dispatch_print_job(printer_address, temp_path)
        temp_path.unlink(missing_ok=True)

        flash(message, "success" if success else "error")
        return redirect(url_for("index"))

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
