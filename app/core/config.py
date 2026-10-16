"""Flags do ambiente de execução do servidor."""

from ..config import AMBIENTE

IS_DEV = AMBIENTE in {"DEV", "DEVELOPMENT"}
IS_TEST = AMBIENTE in {"TEST", "TESTING"}
IS_PRODUCTION = AMBIENTE in {"PROD", "PRODUCTION"}

__all__ = ["IS_DEV", "IS_TEST", "IS_PRODUCTION"]
