import os
import unittest
from pathlib import Path

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

from app.middlewares.registrando_endpoint import register_url


class ErrorResponseFormatTests(unittest.TestCase):
    def setUp(self) -> None:
        template_folder = Path(__file__).resolve().parents[1] / "app" / "templates"
        self.app = Flask(__name__, template_folder=str(template_folder))
        self.app.after_request(register_url)

        @self.app.get("/api/test-error")
        def test_error() -> tuple[dict[str, str], int]:
            return {"message": "erro"}, 400

        self.client = self.app.test_client()

    def test_browser_request_receives_html_error_page(self) -> None:
        response = self.client.get(
            "/api/test-error",
            headers={"Accept": "text/html"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.mimetype, "text/html")
        self.assertIn(b"<!doctype html>", response.data)

    def test_json_request_keeps_json_error_body(self) -> None:
        response = self.client.get(
            "/api/test-error",
            headers={"Accept": "application/json"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(response.get_json(), {"message": "erro"})

    def test_json_request_with_wildcard_keeps_json_error_body(self) -> None:
        response = self.client.get(
            "/api/test-error",
            headers={"Accept": "application/json, */*;q=0.8"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(response.get_json(), {"message": "erro"})


if __name__ == "__main__":
    unittest.main()
