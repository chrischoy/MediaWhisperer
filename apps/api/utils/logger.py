import logging
import os
from datetime import datetime
from pathlib import Path


def get_logger(name: str) -> logging.Logger:
    """
    Create a logger with custom formatting that shows:
    - Timestamp
    - Filename (without extension)
    - Truncated path
    - Line number
    """
    logger = logging.getLogger(name)

    # Prevent propagation to root logger to avoid double logging
    logger.propagate = False

    # Only add handler if logger doesn't already have handlers
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # Custom formatter
        class TruncatedPathFormatter(logging.Formatter):
            def format(self, record):
                # Get the relative path from the workspace root
                workspace_root = Path(__file__).parent.parent.parent
                try:
                    # Get the caller's file path
                    caller_path = Path(record.pathname)
                    # Get relative path from workspace root
                    relative_path = caller_path.relative_to(workspace_root)
                    # Truncate the path to show only last 2 directories
                    path_parts = relative_path.parts
                    if len(path_parts) > 2:
                        truncated_path = os.path.join(*path_parts[-2:])
                    else:
                        truncated_path = str(relative_path)
                    # Get filename without extension
                    filename = Path(record.pathname).stem
                    # Format the message
                    record.truncated_path = truncated_path
                    record.filename = filename
                    # Call parent format to set asctime
                    super().format(record)
                    return f"[{record.asctime}] [{record.truncated_path}] [{record.filename}:{record.lineno}] {record.getMessage()}"
                except Exception:
                    # Fallback to basic format if path processing fails
                    super().format(record)
                    return f"[{record.asctime}] {record.getMessage()}"

        # Set the formatter
        formatter = TruncatedPathFormatter(
            fmt="%(asctime)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(console_handler)

    return logger


# Example usage:
# logger = get_logger(__name__)
# logger.debug("This is a debug message")
# logger.info("This is an info message")
# logger.warning("This is a warning message")
# logger.error("This is an error message")
