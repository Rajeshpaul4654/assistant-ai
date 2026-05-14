"""
logger.py — Centralized logging for JARVIS.
Using Python's built-in logging instead of print()
gives us timestamps, log levels, and clean output.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
import sys

def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger for any module.
    
    Usage in any file:
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("JARVIS started")
    """
    logger = logging.getLogger(name)

    # Only configure if no handlers exist
    # (prevents duplicate log messages)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        # Console handler — prints to terminal
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Format: time + level + module + message
        # Example: 13:07:22 [INFO] brain.llm: JARVIS responded
        formatter = logging.Formatter(
            fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler — persistent rotating logs
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        log_dir = os.path.join(base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "jarvis.log")

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=1_000_000,
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger