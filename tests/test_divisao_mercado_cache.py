import asyncio
import os
import unittest

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

from app.cache.cache import CacheManager
from app.clients.divisao_mercado import _endpoint


class DivisaoMercadoCacheTests(unittest.TestCase):
    def test_endpoint_preserves_full_url(self) -> None:
        url = (
            "https://script.google.com/macros/s/deployment-id/exec/escritorios"
            "?origem=api"
        )

        self.assertEqual(_endpoint(url), url)

    def test_endpoint_expands_deployment_id(self) -> None:
        self.assertEqual(
            _endpoint("deployment-id"),
            "https://script.google.com/macros/s/deployment-id/exec",
        )

    def test_endpoint_leaves_other_urls_unchanged(self) -> None:
        url = "https://example.com/api/escritorios"

        self.assertEqual(_endpoint(url), url)

    def test_get_or_set_caches_market_metadata(self) -> None:
        payload = {
            "recurso": "escritorio",
            "path": "escritorio",
            "aba": "[backend] Divisão oGX & MXP | Escritórios",
            "total": 1,
            "dados": [{"nome": "ABC", "oGT": "MC BAZI", "oGV": "MC BAZI"}],
        }
        cache = CacheManager()

        async def fetch() -> tuple[int, dict[str, object]]:
            return 200, payload

        cached_payload, status = asyncio.run(
            cache.get_or_set("metadados_escritorios", fetch=fetch)
        )

        self.assertEqual(status, 200)
        payload["dados"][0]["nome"] = "Abc"
        self.assertEqual(cached_payload, payload)
        self.assertEqual(
            cache.store["metadados_escritorios"]["data"],
            payload,
        )

    def test_invalid_market_metadata_is_rejected(self) -> None:
        payload = {
            "recurso": "escritorios",
            "path": "base/escritorios",
            "aba": "Escritorios",
            "total": "1",
            "dados": [],
        }

        self.assertIsNone(CacheManager._normalize(payload))


if __name__ == "__main__":
    unittest.main()
