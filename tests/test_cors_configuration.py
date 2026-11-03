import os
import unittest
from unittest.mock import patch

for key, value in {
    "AMBIENTE": "TEST",
    "CACHE_TTL": "3600",
    "APPSCRIPT_B2C": "https://example.test/b2c",
    "APPSCRIPT_DIVISAO_MERCADO": "https://example.test/market",
    "APPSCRIPT_EXPA": "https://example.test/expa",
    "TOKEN_EXPA": "test-token",
    "DOMINIOS_PERMITIDOS": "example.test",
}.items():
    os.environ.setdefault(key, value)

from app import main


class CorsConfigurationTests(unittest.TestCase):
    def test_converts_allowed_domains_to_explicit_origins(self) -> None:
        with patch.object(
            main,
            "DOMINIOS_PERMITIDOS",
            [
                "front.example.test",
                "https://admin.example.test",
                "localhost:3000",
            ],
        ):
            origins = main._origens_cors_permitidas()

        self.assertEqual(
            origins,
            [
                "http://localhost:3000",
                "https://admin.example.test",
                "https://front.example.test",
                "https://localhost:3000",
            ],
        )

    def test_ignores_invalid_or_path_based_entries(self) -> None:
        with patch.object(
            main,
            "DOMINIOS_PERMITIDOS",
            [
                "https://valid.example.test",
                "javascript://invalid.example.test",
                "https://example.test/path",
                "https://",
            ],
        ):
            origins = main._origens_cors_permitidas()

        self.assertEqual(origins, ["https://valid.example.test"])
