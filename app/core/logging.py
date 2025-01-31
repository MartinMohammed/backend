import logging
import json
from datetime import datetime
import os
from pathlib import Path
import sys
import traceback
from typing import Dict, Any

class CustomFormatter(logging.Formatter):
    """Custom formatter that includes extra fields in the message"""
    def format(self, record: logging.LogRecord) -> str:
        # Get the original message
        message = super().format(record)
        
        # If there are extra fields, append them to the message
        if hasattr(record, 'extra'):
            extras = ' | '.join(f"{k}={v}" for k, v in record.extra.items())
            message = f"{message} | {extras}"
            
        return message

def setup_logging() -> None:
    """Configure logging with custom formatter"""
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create formatters
    console_formatter = CustomFormatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_formatter = CustomFormatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    
    # Configure file handler
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_handler = logging.FileHandler(
        logs_dir / f'app_{current_time}.log',
        encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove any existing handlers
    root_logger.handlers = []
    
    # Add our handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name"""
    return logging.getLogger(name)

class LoggerMixin:
    """Mixin to add logging capabilities to a class"""
    @classmethod
    def get_logger(cls) -> logging.Logger:
        return get_logger(cls.__name__)
    
    @property
    def logger(self) -> logging.Logger:
        return get_logger(self.__class__.__name__) 