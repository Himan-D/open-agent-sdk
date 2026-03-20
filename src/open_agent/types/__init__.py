"""Types module - Common type definitions."""

from typing import TypeAlias, Union, Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


@dataclass
class Config:
    """Base configuration class."""
    pass


class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


MessageContent: TypeAlias = Union[str, Dict[str, Any], List[Dict[str, Any]]]
