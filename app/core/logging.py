import logging
import os
from datetime import datetime
from app.core.config import settings

def setup_logging():
    os.makedirs(settings.LOGS_DIR, exist_ok=True)
    log_filename = os.path.join(settings.LOGS_DIR, f"quran_reel_{datetime.now().strftime('%Y%m%d')}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # helper to get logger
    return logging.getLogger("quran_reels")
