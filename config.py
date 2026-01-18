from pathlib import Path
import json
from typing import Union
import os
import logging


class Config:
    # Overall
    ROOT_PATH: Path = Path(__file__).resolve().parent
    MODELS_FOLDER: Union[str, Path] = fr"{ROOT_PATH}/models"
    AUDIO_FILES_FOLDER: Union[str, Path] = fr"{ROOT_PATH}/audio_files"
    LOG_FOLDER: Union[str, Path] = fr"{ROOT_PATH}/logs"

    # Model
    FRAME_LENGTH: int = 256
    FRAME_STEP: int = 160
    FFT_LENGTH: int = 384
    MODEL_FOLDER: str = f"{MODELS_FOLDER}/model7"

    # API
    API_PORT: int = 5000
    API_HOST: str = "127.0.0.1"
    API_LOG_FILE: str = f"{ROOT_PATH}/logs/api_logs.log"
    MAX_IMAGE_FILES: int = 10
    API_MAX_FILE_SIZE_MB = 50
    API_PROTOCOL: str = "http"
    API_ALLOWED_EXTENSIONS = {"wav", "mp3", "ogg", "flac", "m4a", "wav"}
    API_CHECK_INTERVAL: int = 10

    # WEB APP
    WEB_APP_PORT: int = 8000
    WEB_APP_HOST: str = "127.0.0.1"
    WEB_APP_DEBUG: bool = True
    WEB_APP_LOG_FILE: str = f"{ROOT_PATH}/logs/web_app.logs"
    WEB_APP_TEMP_UPLOADS_FOLDER = f"{ROOT_PATH}/webapp/static/temp_uploads"
    WEB_APP_FILES_LIFE_TIME: int = 300
    WEB_APP_USE_SSL: bool = False
    WEB_APP_SSL_FOLDER: str = f"{ROOT_PATH}/ocr_webapp/ssl_cert"
    WEB_APP_TESTING: bool = False
    WEB_APP_PROTOCOL: str = "http"
    WEB_APP_API_TIMEOUT: int = 60

    # LOGGER
    UVICORN_LOG_CONFIG_PATH: Union[str, os.PathLike, Path] = f"{ROOT_PATH}/api/uvicorn_log_config.json"
    CLI_LOG_LEVEL: int = logging.DEBUG
    FILE_LOG_LEVEL: int = logging.DEBUG

    def get_uvicorn_logger(self) -> dict:
        with open(self.UVICORN_LOG_CONFIG_PATH) as f:
            log_config = json.load(f)
            log_config["handlers"]["file_handler"]["filename"] = f"{Config.ROOT_PATH}/logs/api_logs.log"
            return log_config
