import logging
import httpx
from typing import Dict, Any, Tuple
from ..conftest import retry_until, TEST_TIMEOUTS

async def create_application(
    client: httpx.AsyncClient,
    payload: Dict[str, Any],
    idempotency_key: str
) -> httpx.Response:
    """Create an application with the given payload and idempotency key."""
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
        raise

async def create_test_application(
    client: httpx.AsyncClient,
    name: str,
    description: str,
    idempotency_key: str
) -> Tuple[httpx.Response, Dict[str, Any]]:
    """
    Helper to create a test application and return both response and parsed data.
    """
    payload = {
        "name": name,
        "description": description
    }
    response = await client.post(
        "/applications",
        json=payload,
        headers={"Idempotency-Key": idempotency_key}
    )
    data = response.json() if response.status_code == 201 else None
    return response, data

async def update_application(
    client: httpx.AsyncClient,
    app_id: str,
    etag: str,
    updates: Dict[str, Any],
    force: bool = False
) -> httpx.Response:
    """
    Helper to update an application with proper headers.
    """
    params = {"force": "true"} if force else None
    return await client.patch(
        f"/applications/{app_id}",
        json=updates,
        headers={"If-Match": etag},
        params=params
    )

async def verify_application_state(
    client: httpx.AsyncClient,
    app_id: str,
    expected_state: Dict[str, Any]
) -> bool:
    """
    Helper to verify application's current state matches expected state.
    """
    response = await client.get(f"/applications/{app_id}")
    current_state = response.json()
    return all(current_state.get(k) == v for k, v in expected_state.items())

async def wait_for_activation_state(
    client: httpx.AsyncClient,
    app_id: str,
    expected_active: bool,
    timeout: float = TEST_TIMEOUTS['activation']
) -> bool:
    """
    Helper to wait for application to reach expected activation state.
    """
    async def check_activation():
        response = await client.get(f"/applications/{app_id}")
        current_state = response.json()
        return current_state["is_active"] == expected_active
    
    return await retry_until(check_activation, timeout, TEST_TIMEOUTS['retry_interval'])