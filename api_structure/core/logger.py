from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import contextvars
import time
import logging
import os


# Setup logger
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
LOG_PATH = os.path.join(BASE_DIR, "api_structure.log")


class SuppressGoogleAuthInfoFilter(logging.Filter):
    """Filter to suppress Google auth info messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records."""
        return (
            "The user provided Google Cloud credentials"
            not in record.getMessage()
        )


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

for handler in logging.getLogger().handlers:
    handler.addFilter(SuppressGoogleAuthInfoFilter())

# Suppress noisy loggers
for noisy_logger in [
    "azure.core.pipeline.policies.http_logging_policy",
    "azure.core.pipeline",
    "azure.cosmos",
    "azure.identity",
    "azure",
    "openai",
    "httpx",
    "google.auth",
    "google.auth._default",
    "google.genai",
    "google.api_core.client_info",
    "google.api_core.bidi",
    "google.cloud",
]:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

# Export logger
logger = logging.getLogger(__name__)


_log_ctx_var: contextvars.ContextVar = contextvars.ContextVar(
    "log_ctx", default=None
)
VER = "1.0"  # 改成你專案的名稱


@dataclass
class LogContext:
    """Log context for request tracking."""

    case_id: str  # 改成你專案的名稱
    start_time: float
    end_time: float
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    extract_log: Optional[Dict[str, Any]]
    error_log: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "_id": f"{self.case_id}_{int(time.time())}",
            "case_id": self.case_id,
            "version": VER,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "extract_log": self.extract_log or {},
            "error_log": self.error_log or [],
        }


def create_log_context(input_data: Dict[str, Any]) -> LogContext:
    """Create a new log context.

    Args:
        input_data: Input data dictionary.

    Returns:
        LogContext instance.

    Raises:
        ValueError: If case_id is missing.
    """
    case_id = input_data.get("case_id", "no_case_id")
    if not case_id:  # 改成你專案的名稱
        raise ValueError("input_data must contain 'case_id'")

    ctx = LogContext(
        case_id=case_id,
        start_time=round(time.time(), 4),
        end_time=round(time.time(), 4),
        input_data=input_data or {},
        output_data=None,
        extract_log=None,
        error_log=[],
    )
    _log_ctx_var.set(ctx)
    return ctx


def get_log_context() -> LogContext:
    """
    Get the current log context from contextvars.

    Returns:
        LogContext: Current request's log context
    """
    ctx = _log_ctx_var.get()
    if ctx is None:
        return create_log_context({})
    return ctx


def set_extract_log(extract_log: Dict[str, Any]) -> None:
    """
    Set extract log for additional processing details.

    Args:
        extract_log: Dictionary containing intermediate processing information
    """
    ctx = get_log_context()
    ctx.extract_log = extract_log


def set_end_time() -> None:
    """
    Set the end time for the current request.
    Automatically called by middleware when request completes.
    """
    ctx = get_log_context()
    ctx.end_time = round(time.time(), 4)
