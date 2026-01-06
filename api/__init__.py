import sys
from pathlib import Path
import os
from logging import Logger
sys.path.append(str(Path(__file__).resolve().parent.parent))
from fastapi import FastAPI

from config import Config
from custom_logger import CustomLogger
from speech_text import SpeechToText


def setup_logging() -> Logger:
    """Configure logging for the api"""
    log_dir = os.path.dirname(Config.API_LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = CustomLogger(
        logger_name="middleware_logger",
        logger_log_level=Config.CLI_LOG_LEVEL,
        file_handler_log_level=Config.FILE_LOG_LEVEL,
        log_file_name=Config.API_LOG_FILE
    ).create_logger()

    return logger

logger = setup_logging()
logger.info("Starting api...")

app = FastAPI(title="OcrDocumentsApi")
logger.info("Starting speech to text module")
speech_to_text = SpeechToText(
    model_folder=Config.MODEL_FOLDER
)
logger.info("Speech to text module loaded")

from api import routes
logger.info("Api started")