import asyncio

import pytest


class MockResponse:
    status_code = 200
    text = "<html><title>Test</title><body>Hello world</body></html>"


class MockClient:
    async def get(self, url):
        return MockResponse()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        pass

    async def aclose(self):
        pass


@pytest.fixture
def mock_async_client(monkeypatch):
    def _make_client(*args, **kwargs):
        return MockClient()

    monkeypatch.setattr("crawler.core.crawler.httpx.AsyncClient", _make_client)
    return _make_client
