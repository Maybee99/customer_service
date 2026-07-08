import logging
import sys
import os
from ..config import get_settings

settings = get_settings()


class _SafeStreamHandler(logging.StreamHandler):
    """StreamHandler that handles Unicode characters safely on any console.

    Tries to write the message directly first. If the stream's encoding
    can't handle some characters (UnicodeEncodeError), falls back to
    encoding with the stream's codec + 'replace' error handling.
    """

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            stream = self.stream
            # Try direct write first — works for all chars in the stream's encoding
            try:
                stream.write(msg + self.terminator)
            except UnicodeEncodeError:
                # Some chars can't be encoded in the stream's codec (e.g. GBK).
                # Re-encode safely: characters outside the codec become '?'
                encoding = getattr(stream, 'encoding', 'utf-8') or 'utf-8'
                safe = msg.encode(encoding, errors='replace').decode(encoding)
                stream.write(safe + self.terminator)
            self.flush()
        except Exception:
            pass


def setup_logger(name: str = "customer_service") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Always replace handlers with SafeStreamHandler to avoid Unicode crashes
    for h in list(logger.handlers):
        logger.removeHandler(h)

    handler = _SafeStreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(handler)

    return logger


logger = setup_logger()
