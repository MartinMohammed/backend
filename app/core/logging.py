import logging
import json
from datetime import datetime
import os

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

def setup_logging() -> None:
    """Configure logging for the application"""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    logger = logging.getLogger("game_jam")
    logger.setLevel(logging.DEBUG)

    # Console handler with JSON formatting
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

    # File handler for persistent logs
    file_handler = logging.FileHandler("logs/game_jam.log")
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

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