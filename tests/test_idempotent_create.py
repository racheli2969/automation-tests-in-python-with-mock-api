import asyncio
import pytest
import logging
from typing import List, Dict, Any, AsyncGenerator
import httpx
from .conftest import TEST_TIMEOUTS, respect_retry_after, retry_until
from .helpers.application_helpers import create_application, create_test_application

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# Constants for test configuration
CONCURRENT_REQUEST_COUNT = 4
EXCEED_RATE_LIMIT_COUNT = 7

async def make_concurrent_post_request(
    client: httpx.AsyncClient,
    payload: Dict[str, Any],
    idempotency_key: str
) -> httpx.Response:
    """Make a concurrent request with proper error handling."""
    try:
        return await create_application(
            client,
            payload,
            idempotency_key
        )
    except Exception as e:
        print(f"Request failed with exception: {type(e).__name__}: {str(e)}")
        return e
        
def process_responses(responses):
    """
    Process response list and categorize them.
    
    Args:
        responses: List of responses from concurrent requests
        
    Returns:
        Tuple of (successful_responses, status_codes, error_responses)
    """
    successful_responses = []
    status_codes = []
    error_responses = []
    
    logging.info(f"\nProcessing {len(responses)} concurrent responses:")
    
    for i, response in enumerate(responses):
        if isinstance(response, Exception):
            logging.error(f"  ❌ Request {i} failed with exception: {type(response).__name__}: {str(response)}")
            error_responses.append(str(response))
        else:
            status_codes.append(response.status_code)
            if response.status_code == 201:
                logging.info(f"  ✓ Request {i}: Created (201)")
                successful_responses.append(response)
            else:
                try:
                    error_content = response.text
                    error_responses.append(error_content)
                    logging.warning(f"  ⚠ Request {i}: Status {response.status_code} - {error_content}")
                except Exception as e:
                    logging.error(f"  ❌ Request {i}: Could not read error content: {e}")
                    error_responses.append(str(e))
    
    logging.info(f"\nSummary: {len(successful_responses)} successful, {len(error_responses)} failed")
    return successful_responses, status_codes, error_responses
    
        


@pytest.mark.asyncio
@pytest.mark.timeout(TEST_TIMEOUTS['test_function'])
async def test_concurrent_requests_same_idempotency(
    initialized_client: AsyncGenerator[httpx.AsyncClient, None],
    generate_idempotency_key
):
    """
    Test that concurrent requests with the same idempotency key create only one resource.
    
    Verifies that when multiple concurrent requests are made with the same idempotency key
    and payload, only one resource is created and all responses are identical.
    """
    client = await anext(initialized_client)
    logging.info("\n=== Testing Concurrent Requests with Same Idempotency Key ===")    
    idempotency_key = generate_idempotency_key()
    test_id = generate_idempotency_key()
    concurrent_payload = {
        "name": f"Test_App{test_id[:8]}".lower(),
        "description": "Test app for idempotent concurrency test"
    }
    logging.info(f"Testing with unique app name: {concurrent_payload['name']}")
   
    # Send N parallel requests with the same idempotency key
    responses = await asyncio.gather(
        *[make_concurrent_post_request(client, concurrent_payload, idempotency_key)
          for _ in range(CONCURRENT_REQUEST_COUNT)],
        return_exceptions=True
    )
    successful_responses, status_codes, error_responses = process_responses(responses)
    
    # Verify all successful responses are identical
    assert len(successful_responses) > 0, "No successful responses received"
    first_response = successful_responses[0]
    first_response_data = first_response.json()
    first_id = first_response_data["id"]
    
    for response in successful_responses[1:]:
        response_data = response.json()
        assert response_data["id"] == first_id, f"Different resource created: {response_data['id']} != {first_id}"
        assert response_data == first_response_data, "Response data differs for same idempotency key"
    
    return first_response_data  # Return for use in negative idempotency test

@pytest.mark.asyncio
@pytest.mark.timeout(TEST_TIMEOUTS['test_function'])
async def test_rate_limiting_with_retry(
    initialized_client: AsyncGenerator[httpx.AsyncClient, None],
    generate_idempotency_key
):
    """
    Test rate limiting behavior with retry mechanism.
    
    Verifies:
    1. Rate limit is enforced (429 response)
    2. Retry-After header is present and valid
    3. Requests succeed after respecting retry delay
    """
    client = await anext(initialized_client)
    logging.info("\n=== Testing Rate Limiting with Retry Mechanism ===")
    
    test_uuid = generate_idempotency_key()
    hit_rate_limit = False

    for i in range(EXCEED_RATE_LIMIT_COUNT):
        rate_limit_key = generate_idempotency_key()
        payload = {
            "name": f"Rate_Test_App_{test_uuid[:8]}_{i}".lower(),
            "description": "Rate limit test"
        }
        
        response = await create_application(
            client,
            payload,
            rate_limit_key
        )

        if response.status_code == 429:
            hit_rate_limit = True
            assert "Retry-After" in response.headers, "429 response missing Retry-After header"
            retry_after = int(response.headers["Retry-After"])
            assert retry_after > 0, "Retry-After value must be positive"

            # Wait and retry
            await respect_retry_after(response)
            
            async def check_success():
                retry_response = await create_application(
                    client,
                    payload,
                    rate_limit_key
                )
                return retry_response.status_code == 201

            success = await retry_until(
                check_success, 
                timeout=TEST_TIMEOUTS['retry'], 
                interval=TEST_TIMEOUTS['retry_interval']
            )
            assert success, f"Failed to create application '{payload['name']}' after retries"
    
    assert hit_rate_limit, "Expected to hit rate limit at least once"

@pytest.mark.asyncio
@pytest.mark.timeout(TEST_TIMEOUTS['test_function'])
async def test_negative_idempotency(
    initialized_client: AsyncGenerator[httpx.AsyncClient, None],
    generate_idempotency_key
):
    """
    Test negative idempotency case where same key is used with different payload.
    
    Verifies that using the same idempotency key with a different payload
    returns the original resource without modification.
    """
    client = await anext(initialized_client)
    logging.info("\n=== Testing Negative Idempotency ===")
    
    # First create an initial application
    idempotency_key = generate_idempotency_key()
    initial_payload = {
        "name": f"Original_App_{generate_idempotency_key()[:8]}".lower(),
        "description": "Original application"
    }
    
    initial_response = await create_application(
        client,
        initial_payload,
        idempotency_key
    )
    assert initial_response.status_code == 201
    initial_data = initial_response.json()
    
    # Try to create different application with same idempotency key
    different_payload = {
        "name": f"Different_App_{generate_idempotency_key()[:8]}".lower(),
        "description": "Different payload test with same idempotency key"
    }
    different_response = await create_application(
        client,
        different_payload,
        idempotency_key
    )
    
    # Should return the original response
    assert different_response.status_code in (200, 201)
    response_data = different_response.json()
    
    assert response_data["id"] == initial_data["id"], (
        "Returned different resource ID for same idempotency key"
    )
    assert response_data == initial_data, (
        "Response data differs from original for same idempotency key"
    )
    assert response_data["name"] != different_payload["name"], (
        "Name was incorrectly updated for same idempotency key"
    )