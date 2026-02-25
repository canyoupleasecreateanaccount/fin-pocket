"""fin-pocket: Technical analysis signal visualization tool for stocks."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("fin-pocket")
except PackageNotFoundError:
    __version__ = "0.0.0.dev0"
