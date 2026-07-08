 import logging
 import sys
 from app.config import get_settings

 settings = get_settings()


 def setup_logger(name: str = "customer_service") -> logging.Logger:
     logger = logging.getLogger(name)
     logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

     if not logger.handlers:
         handler = logging.StreamHandler(sys.stdout)
         handler.setFormatter(logging.Formatter(
             "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
             datefmt="%Y-%m-%d %H:%M:%S",
         ))
         logger.addHandler(handler)

     return logger


 logger = setup_logger()
