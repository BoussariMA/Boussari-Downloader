import logging
import json
from datetime import datetime, timezone
import os

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        return json.dumps(log_record)

def setup_logger():
    logger = logging.getLogger("LinuxDownloader")
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JsonFormatter())
    logger.addHandler(console_handler)
    
    log_dir = os.environ.get("XDG_STATE_HOME", os.path.join(os.path.expanduser("~"), ".local", "state"))
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "boussari_downloader_debug.log")
    file_handler = logging.FileHandler(log_path, mode="w")
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logger()
