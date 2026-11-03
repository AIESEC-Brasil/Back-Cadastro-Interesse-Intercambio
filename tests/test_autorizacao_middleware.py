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


class ForwardedHostAuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = Flask(__name__)

    def test_blocks_forwarded_host_not_in_allowed_domains(self) -> None:
        with (
            self.app.test_request_context(
                "/new-lead-ogx/cadastro-b2c",
                method="POST",
                headers={
                    "Host": "example.test",
                    "X-Forwarded-Host": "untrusted.example",
                },
            ),
            patch.object(autorizacao, "IS_PRODUCTION", False),
            patch.object(autorizacao, "IS_TEST", False),
            patch.object(autorizacao, "API_KEYS_PERMITIDAS", []),
            patch.object(autorizacao, "DOMINIOS_PERMITIDOS", ["example.test"]),
        ):
            response, status = autorizacao.verificar_origem()

        self.assertEqual(status, 401)
        self.assertEqual(response.get_json(), {"error": "Domínio não autorizado"})

    def test_allows_forwarded_host_matching_allowed_domain(self) -> None:
        with (
            self.app.test_request_context(
                "/new-lead-ogx/cadastro-b2c",
                method="POST",
                headers={
                    "Host": "example.test",
                    "X-Forwarded-Host": "example.test",
                },
            ),
            patch.object(autorizacao, "IS_PRODUCTION", False),
            patch.object(autorizacao, "IS_TEST", False),
            patch.object(autorizacao, "API_KEYS_PERMITIDAS", []),
            patch.object(autorizacao, "DOMINIOS_PERMITIDOS", ["example.test"]),
        ):
            result = autorizacao.verificar_origem()

        self.assertIsNone(result)

    def test_prefers_forwarded_host_over_upstream_host(self) -> None:
        with (
            self.app.test_request_context(
                "/new-lead-ogx/cadastro-b2c",
                method="POST",
                headers={
                    "Host": "backend.internal",
                    "X-Forwarded-Host": "untrusted.example",
                },
            ),
            patch.object(autorizacao, "IS_PRODUCTION", False),
            patch.object(autorizacao, "IS_TEST", False),
            patch.object(autorizacao, "API_KEYS_PERMITIDAS", []),
            patch.object(autorizacao, "DOMINIOS_PERMITIDOS", ["example.test"]),
        ):
            response, status = autorizacao.verificar_origem()

        self.assertEqual(status, 401)
        self.assertEqual(response.get_json(), {"error": "Domínio não autorizado"})

    def test_uses_host_when_forwarded_host_is_missing(self) -> None:
        with (
            self.app.test_request_context(
                "/new-lead-ogx/cadastro-b2c",
                method="POST",
                headers={"Host": "untrusted.example"},
            ),
            patch.object(autorizacao, "IS_PRODUCTION", False),
            patch.object(autorizacao, "IS_TEST", False),
            patch.object(autorizacao, "API_KEYS_PERMITIDAS", []),
            patch.object(autorizacao, "DOMINIOS_PERMITIDOS", ["example.test"]),
        ):
            response, status = autorizacao.verificar_origem()

        self.assertEqual(status, 401)
        self.assertEqual(response.get_json(), {"error": "Domínio não autorizado"})

    def test_uses_authority_when_forwarded_host_is_missing(self) -> None:
        with (
            self.app.test_request_context(
                "/new-lead-ogx/cadastro-b2c",
                method="POST",
                headers={":authority": "untrusted.example"},
            ),
            patch.object(autorizacao, "IS_PRODUCTION", False),
            patch.object(autorizacao, "IS_TEST", False),
            patch.object(autorizacao, "API_KEYS_PERMITIDAS", []),
            patch.object(autorizacao, "DOMINIOS_PERMITIDOS", ["example.test"]),
        ):
            response, status = autorizacao.verificar_origem()

        self.assertEqual(status, 401)
        self.assertEqual(response.get_json(), {"error": "Domínio não autorizado"})

    def test_uses_http_authority_from_wsgi_environment(self) -> None:
        with (
            self.app.test_request_context(
                "/new-lead-ogx/cadastro-b2c",
                method="POST",
                environ_overrides={"HTTP_AUTHORITY": "example.test"},
            ),
            patch.object(autorizacao, "IS_PRODUCTION", False),
            patch.object(autorizacao, "IS_TEST", False),
            patch.object(autorizacao, "API_KEYS_PERMITIDAS", []),
            patch.object(autorizacao, "DOMINIOS_PERMITIDOS", ["example.test"]),
        ):
            result = autorizacao.verificar_origem()

        self.assertIsNone(result)
