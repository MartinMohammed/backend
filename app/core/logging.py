import logging
import json
from datetime import datetime
import os
import sys
from logging.handlers import RotatingFileHandler
from .config import settings

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add extra fields if they exist
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

def setup_logging():
    """Configure logging based on the environment"""
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Set up basic configuration
    log_level = getattr(logging, settings.LOG_LEVEL.upper())
    
    # Format based on environment
    if settings.ENV == "prod":
        log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
    else:
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        date_format = '%H:%M:%S'
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            # Console handler
            logging.StreamHandler(sys.stdout),
            # File handler with rotation
            RotatingFileHandler(
                f"{log_dir}/{settings.ENV}.log",
                maxBytes=10485760,  # 10MB
                backupCount=5,
                encoding="utf-8"
            )
        ]
    )
    
    # Set third-party loggers to WARNING in production
    if settings.ENV == "prod":
        for logger_name in ["uvicorn", "gunicorn", "fastapi"]:
            logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    # Create logger for the application
    logger = logging.getLogger("game-jam")
    logger.setLevel(log_level)
    
    return logger

# Create the logger instance
logger = setup_logging()

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(f"game_jam.{name}")

class LoggerMixin:
    """Mixin to add logging capabilities to a class"""
    @classmethod
    def get_logger(cls) -> logging.Logger:
        """Get a logger for the class"""
        if not hasattr(cls, "_logger"):
            cls._logger = get_logger(cls.__name__)
        return cls._logger

    @property
    def logger(self) -> logging.Logger:
        """Get a logger for the instance"""
        return self.get_logger() 