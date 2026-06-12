import importlib.metadata as metadata

from .plugin import get_describe_functions
from .shared import behaves_like

__all__ = ["behaves_like", "get_describe_functions"]

try:
    __version__: str = metadata.version("pytest-describe")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0+unknown"
