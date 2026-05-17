"""Auto Agent — CLI tool for creating and managing autonomous AI agents."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("auto-agent")
except PackageNotFoundError:
    __version__ = "0.1.0"  # fallback for development
