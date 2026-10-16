"""Flags do ambiente."""

from .config import DOMINIOS_PERMITIDOS, IS_DEV, IS_PRODUCTION, IS_TEST
from .logger import setup_logging

__all__ = ["DOMINIOS_PERMITIDOS", "IS_DEV", "IS_PRODUCTION", "IS_TEST", "setup_logging"]
