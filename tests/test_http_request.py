import asyncio
import os
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

import httpx

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

from app.clients.http_request import HttpClient


class HttpClientLifecycleTests(IsolatedAsyncioTestCase):
    async def test_skips_closing_client_when_its_event_loop_is_closed(self) -> None:
        client = HttpClient()
        old_client = AsyncMock(spec=httpx.AsyncClient)
        old_loop = asyncio.new_event_loop()
        old_loop.close()
        client._active_client = old_client
        client._loop_associado = old_loop

        try:
            active_client = await client._get_client()

            old_client.aclose.assert_not_awaited()
            self.assertIsNot(active_client, old_client)
        finally:
            await client.close()
