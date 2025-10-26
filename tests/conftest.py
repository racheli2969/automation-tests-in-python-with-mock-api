import asyncio
import os
import pytest
import uuid
import httpx
import time
import logging
from typing import AsyncGenerator, Callable, Dict, Any
import uvicorn
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from mock_api.app import app

# Shared Test Constants
TEST_TIMEOUTS = {
    'test_function': 200,    # Overall test timeout
    'retry': 60,           # Maximum retry time
    'activation': 2.5,     # Activation check timeout
    'retry_interval': 0.1  # Time between retries
}

CONCURRENT_REQUESTS = {
    'default': 4,    # Default number of concurrent requests
    'stress': 10,    # Stress testing
    'rate_limit': 7  # Number of requests to trigger rate limit
}

# Response Status Codes
STATUS = {
    'success': [200, 201, 202],
    'rate_limit': 429,
    'conflict': 409,
    'precondition': 412,
    'validation': 422
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def server():
    """Start the API server as a fixture."""
    config = uvicorn.Config(app,
                            host="127.0.0.1",
                            port=8000,
                            log_level="error",
                            lifespan="on"
                            )
    server = uvicorn.Server(config)
     # Start server in background task
    task = asyncio.create_task(server.serve())
    
    # Give the server a moment to start
    await asyncio.sleep(0.1)
    
    yield server
    
    # Cleanup
    server.should_exit = True
    await task
    # await server.startup()
    # yield
    # await server.shutdown()

@pytest.fixture
def base_url():
    """Get the base URL for the API."""
    return "http://127.0.0.1:8000"

@pytest.fixture
def auth_token():
    """Generate a test authentication token."""
    return str(uuid.uuid4())

@pytest.fixture(scope="function")
async def test_http_client(server, base_url, auth_token) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create an HTTP client for testing the API.
    
    Returns a configured httpx.AsyncClient instance with base_url and default headers set.
    The client is created per test function to ensure a clean state.
    """
   
    async with httpx.AsyncClient(
        base_url=base_url,
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    ) as client:
        yield client

@pytest.fixture
async def initialized_client(test_http_client: AsyncGenerator[httpx.AsyncClient, None]) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Fixture to get initialized HTTP client."""
    logging.info("\n=== Initializing Test Client ===")
    client = await anext(test_http_client)
    logging.info("✓ Test client initialized")
    yield client

@pytest.fixture
def generate_idempotency_key() -> Callable[[], str]:
    """Factory fixture to generate unique idempotency keys."""
    def _generate():
        return str(uuid.uuid4())
    return _generate

async def respect_retry_after(response: httpx.Response) -> None:
    """Helper to respect the Retry-After header."""
    if response.status_code == 429:
        retry_after = int(response.headers["Retry-After"])
        await asyncio.sleep(retry_after)

async def retry_until(predicate: Callable[[], bool], timeout: float = 2.5, interval: float = 0.1):
    """Helper to retry an operation until it succeeds or times out."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if await predicate():
            return True
        await asyncio.sleep(interval)
    return False

# Helper functions moved to application_helpers.py