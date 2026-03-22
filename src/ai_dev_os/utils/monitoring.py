import logging


def setup_structured_logging():
    """
    Stub for structured logging setup.
    If python-json-logger is available, it uses it. Otherwise uses standard logging.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Check if we already have a JSON-like formatter
    has_json_formatter = any("Json" in type(h.formatter).__name__ for h in logger.handlers)

    if not has_json_formatter:
        try:
            try:
                from pythonjsonlogger.json import JsonFormatter
            except ImportError:
                from pythonjsonlogger import jsonlogger

                JsonFormatter = jsonlogger.JsonFormatter

            formatter = JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
            logHandler = logging.StreamHandler()
            logHandler.setFormatter(formatter)
            logger.addHandler(logHandler)
        except ImportError:
            # Only add standard formatter if no handlers exist at all
            if not logger.handlers:
                formatter = logging.Formatter(
                    "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
                )
                logHandler = logging.StreamHandler()
                logHandler.setFormatter(formatter)
                logger.addHandler(logHandler)

    return logger
