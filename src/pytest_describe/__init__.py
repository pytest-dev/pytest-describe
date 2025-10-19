import importlib.metadata as metadata

from .shared import behaves_like

__all__ = ["behaves_like"]

try:
    __version__ = metadata.version("pytest-describe")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0+unknown"
