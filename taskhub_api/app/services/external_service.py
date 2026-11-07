import asyncio

import httpx

from app.core.errors import UpstreamError


async def fetch_json_pair(client: httpx.AsyncClient, url_a: str, url_b: str) -> tuple[dict, dict]:
    async def fetch(url: str) -> dict:
        try:
            response = await client.get(url)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise UpstreamError("External service request failed", details={"url": url}) from exc
        if not isinstance(payload, dict):
            raise UpstreamError("External service returned a non-object JSON value", details={"url": url})
        return payload

    return await asyncio.gather(fetch(url_a), fetch(url_b))
