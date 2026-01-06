import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from functools import wraps
import requests
import io
import os
import time
import mimetypes
from flask import render_template, flash, send_from_directory
from requests.exceptions import ConnectionError, Timeout

from config import Config
from webapp import app, forms, api_connected


_api_status_cache = {"connected": False, "last_check": 0}
API_CHECK_INTERVAL = Config.API_CHECK_INTERVAL

def check_api_connection() -> bool:
    """checks connection to api with some cache"""
    now = time.time()
    
    if now - _api_status_cache["last_check"] < API_CHECK_INTERVAL:
        return _api_status_cache["connected"]
    
    try:
        response = requests.get(
            f"http://{Config.API_HOST}:{Config.API_PORT}/health",
            timeout=5
        )
        connected = response.status_code == 200 and response.json().get("status") == "all green"
    except Exception as e:
        app.logger.error(f"API connection check failed: {e}")
        connected = False
    
    _api_status_cache["connected"] = connected
    _api_status_cache["last_check"] = now
    return connected

def require_api_connection(f) -> None:
    """Dekorator sprawdzający połączenie z API."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not check_api_connection():
            flash("API is not available. Try again later.", "danger")
            return render_template("home.html", form=forms.MainForm(), results=[])
        return f(*args, **kwargs)
    return decorated_function

def get_mime_type(filename: str) -> str:
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"

################### FILTERS #################################
# Getting file path
@app.template_filter("basename")
def basename_filter(path):
    return os.path.basename(path)


################### ROUTES #################################
@app.route("/health", methods=["GET"])
def health_check():
    api_status = check_api_connection()
    return {"status": api_status}

# Serve audio
@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_from_directory(Config.WEB_APP_TEMP_UPLOADS_FOLDER, filename)

@app.route("/", methods=["GET", "POST"])
@require_api_connection
def home():
    form = forms.MainForm()
    results = []
    file_names = []

    try:
        if form.validate_on_submit():
            normalize = form.normalize_list_field.data

            file_contents = []
            for audio_file in form.images_field.data:
                content = audio_file.read()
                timestamp = int(time.time())
                filename = f"{timestamp}_{audio_file.filename}"
                file_path = rf"{Config.WEB_APP_TEMP_UPLOADS_FOLDER}\{filename}"

                with open(file_path, "wb") as f:
                    f.write(content)
                file_names.append(filename)
                file_contents.append((content, audio_file.filename))

            files = []
            for content, original_name in file_contents:
                files.append(
                    ("files", (file_path, io.BytesIO(content), get_mime_type(original_name)))
                )
            app.logger.debug(f"Making request with {len(files)} files and {normalize=}")
            response = requests.post(
                f"{Config.API_PROTOCOL}://{Config.API_HOST}:{Config.API_PORT}/get_text",
                params={"normalize": normalize},
                files=files,
                timeout=Config.WEB_APP_API_TIMEOUT
            )

            if response.status_code == 200:
                res = response.json()["result"]
                for transcription, file_name in zip(res, file_names):
                    results.append(
                        {
                            "filename": file_name,
                            "transcription": transcription
                        }
                    )
            else:
                app.logger.error(f"API error: {response.status_code}, {response.json()['detail']}")
                flash(f"API error: {response.status_code}, {response.json()['detail']}", "danger")
    except ConnectionError:
        app.logger.error("API connection error")
        flash("API connection error", "danger")
    except Timeout:
        app.logger.error("API timeout error")
        flash("API timeout error", "danger")
    except Exception as e:
        app.logger.error(f"Unhandled error: {e}")
        flash(f"Unhandled error: {e}", "danger")

    return render_template("home.html",
                           form=form,
                           results=results
                           )