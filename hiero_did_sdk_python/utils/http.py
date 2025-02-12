from typing import Any

from aiohttp import BaseConnector, ClientError, ClientResponse, ClientSession
from aiohttp_retry import ExponentialRetry, RetryClient


async def fetch(
    url: str,
    *,
    headers: dict | None = None,
    retry: bool = True,
    max_attempts: int = 3,
    interval: float = 1.0,
    backoff_factor: float = 1.5,
    connector: BaseConnector | None = None,
    session: ClientSession | None = None,
    json: bool = False,
) -> str | Any:
    """Fetch from an HTTP server with automatic retries.

    Args:
        url: the address to fetch
        headers: an optional dict of headers to send
        retry: flag to retry the fetch
        max_attempts: the maximum number of attempts to make
        interval: the interval between retries, in seconds
        backoff_factor: the backoff interval, in seconds
        connector: an optional existing BaseConnector
        session: a shared ClientSession
        json: flag to parse the result as JSON

    """
    limit = max_attempts if retry else 1
    if not session:
        session = ClientSession(connector=connector, connector_owner=(not connector), trust_env=True)
    async with session:
        retry_options = ExponentialRetry(attempts=limit, start_timeout=interval, factor=backoff_factor)
        async with RetryClient(client_session=session, retry_options=retry_options) as retry_client:
            response: ClientResponse = await retry_client.get(url, headers=headers)
            if response.status < 200 or response.status >= 300:
                raise ClientError(f"Bad response from server: {response.status} - " f"{response.reason}")
            return await (response.json() if json else response.text())
