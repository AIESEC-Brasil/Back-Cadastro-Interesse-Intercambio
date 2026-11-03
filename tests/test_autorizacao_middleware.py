import os
import unittest
from unittest.mock import patch

from flask import Flask

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

from app.middlewares import autorizacao


class OriginAuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = Flask(__name__)

    def test_blocks_origin_not_in_allowed_domains(self) -> None:
        with (
            self.app.test_request_context(
                "/new-lead-ogx/cadastro-b2c",
                method="POST",
                headers={
                    "Host": "example.test",
                    "Origin": "https://untrusted.example",
                },
            ),
            patch.object(autorizacao, "IS_PRODUCTION", False),
            patch.object(autorizacao, "IS_TEST", False),
            patch.object(autorizacao, "API_KEYS_PERMITIDAS", []),
            patch.object(autorizacao, "DOMINIOS_PERMITIDOS", ["example.test"]),
        ):
            response, status = autorizacao.verificar_origem()

        self.assertEqual(status, 401)
        self.assertEqual(response.get_json(), {"error": "Origem não autorizada"})

    def test_allows_origin_matching_allowed_domain_and_port(self) -> None:
        with (
            self.app.test_request_context(
                "/new-lead-ogx/cadastro-b2c",
                method="POST",
                headers={
                    "Host": "example.test",
                    "Origin": "https://example.test",
                },
            ),
            patch.object(autorizacao, "IS_PRODUCTION", False),
            patch.object(autorizacao, "IS_TEST", False),
            patch.object(autorizacao, "API_KEYS_PERMITIDAS", []),
            patch.object(autorizacao, "DOMINIOS_PERMITIDOS", ["example.test"]),
        ):
            result = autorizacao.verificar_origem()

        self.assertIsNone(result)

    def test_rejects_malformed_and_null_origins(self) -> None:
        for origin in ("null", "https://"):
            with self.subTest(origin=origin):
                with (
                    self.app.test_request_context(
                        "/new-lead-ogx/cadastro-b2c",
                        method="POST",
                        headers={"Host": "example.test", "Origin": origin},
                    ),
                    patch.object(autorizacao, "IS_PRODUCTION", False),
                    patch.object(autorizacao, "IS_TEST", False),
                    patch.object(autorizacao, "API_KEYS_PERMITIDAS", []),
                    patch.object(
                        autorizacao, "DOMINIOS_PERMITIDOS", ["example.test"]
                    ),
                ):
                    response, status = autorizacao.verificar_origem()

                self.assertEqual(status, 401)
                self.assertEqual(
                    response.get_json(), {"error": "Origem não autorizada"}
                )
