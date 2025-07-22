import logging
from datetime import datetime

log_data = []

def add_log(speaker, message):
    log_data.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "speaker": speaker,
        "message": message
    })

def get_log():
    return log_data

def setup_logger(name, level=logging.INFO):
    """
    Setup logger untuk komponen StreamMate AI
    """
    logger = logging.getLogger(name)
    
    # Jika logger sudah dikonfigurasi, return saja
    if logger.handlers:
        return logger
    
    # Set level
    logger.setLevel(level)
    
    # Buat formatter
    formatter = logging.Formatter(
        '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Buat console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Buat file handler untuk logs
    try:
        import os
        from pathlib import Path
        
        # Buat direktori logs jika belum ada
        logs_dir = Path(__file__).parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(
            logs_dir / f"{name.lower()}.log",
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    except Exception as e:
        # Jika gagal membuat file handler, gunakan console saja
        pass
    
    return logger

