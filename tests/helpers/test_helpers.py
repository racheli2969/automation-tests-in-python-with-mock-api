import httpx
import logging
from typing import Dict, Any, List
from ..conftest import TEST_TIMEOUTS

async def make_concurrent_requests(
    client: httpx.AsyncClient,
    payload: Dict[str, Any],
    idempotency_key: str,
    count: int
) -> List[httpx.Response]:
    """Make concurrent requests with proper error handling."""
    try:
        response = await client.post(
            "/applications",
            json=payload,
            headers={"Idempotency-Key": idempotency_key}
        )
        logging.info(f"Request returned status: {response.status_code}")
        return response
    except Exception as e:
        logging.error(f"Request failed with exception: {type(e).__name__}: {str(e)}")
        return e