import asyncio
import pytest
import httpx
import uuid
import logging
from typing import AsyncGenerator
from .conftest import TEST_TIMEOUTS
from .helpers.application_helpers import (
    create_test_application,
    update_application,
    verify_application_state,
    wait_for_activation_state
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

@pytest.fixture
async def test_app(
    initialized_client: AsyncGenerator[httpx.AsyncClient, None],
    generate_idempotency_key
):
    """Fixture to create a test application for use in tests."""
    client = await anext(initialized_client)
    response = await client.post(
        "/applications",
        json={
            "name": "test-app-base",
            "description": "Base test application"
        },
        headers={"Idempotency-Key": generate_idempotency_key()}
    )
    return response.json()

@pytest.mark.asyncio
@pytest.mark.timeout(TEST_TIMEOUTS['test_function'])
async def test_name_normalization_and_uniqueness(
    initialized_client: AsyncGenerator[httpx.AsyncClient, None],
    generate_idempotency_key
):
    """
    Test that application names are properly normalized and uniqueness is enforced.
    """
    client = await anext(initialized_client)
    # Create first application with lowercase name
    first_name = "my-test-app"
    _, first_app = await create_test_application(
        client,
        first_name,
        "First test app",
        generate_idempotency_key()
    )
    
    # Try to create second application with same name but different case
    second_response, _ = await create_test_application(
        client,
        first_name.upper(),
        "Second test app",
        generate_idempotency_key()
    )
    
    assert second_response.status_code == 409, (
        "Expected 409 Conflict for normalized name collision"
    )
    
@pytest.mark.asyncio
@pytest.mark.timeout(TEST_TIMEOUTS['test_function'])
async def test_optimistic_locking_concurrent_updates(
    initialized_client: AsyncGenerator[httpx.AsyncClient, None]
):
    """
    Test that concurrent updates with same ETag are handled correctly.
    """
    client = await anext(initialized_client)
    response = await client.post(
        "/applications",
        json={
            "name": "test-app-base",
            "description": "Base test application"
        },
        headers={"Idempotency-Key": str(uuid.uuid4())}
    )
    test_app = response.json()
    initial_etag = test_app["etag"]
    
    # Function to attempt update
    async def update_description():
        return await update_application(
            client,
            test_app["id"],
            initial_etag,
            {"description": "Updated description"}
        )
    
    # Make concurrent update attempts
    responses = await asyncio.gather(
        *[update_description() for _ in range(2)]
    )
    
    # Verify one succeeded and one failed
    statuses = sorted(r.status_code for r in responses)
    assert statuses in [[412, 200], [200, 412]], (
        "Expected one success (200) and one precondition failure (412)"
    )

@pytest.mark.asyncio
@pytest.mark.timeout(TEST_TIMEOUTS['test_function'])
async def test_activation_rules_with_test_name(
    initialized_client: AsyncGenerator[httpx.AsyncClient, None]
):
    """
    Test activation rules when application name contains 'test'.
    """
    client = await anext(initialized_client)
    # Create test application with unique name
    test_id = str(uuid.uuid4())[:8]
    response = await client.post(
        "/applications",
        json={
            "name": f"activation-test-{test_id}",
            "description": "Base test application"
        },
        headers={"Idempotency-Key": str(uuid.uuid4())}
    )
    assert response.status_code == 201, f"Failed to create test app: {response.text}"
    test_app = response.json()
    # First rename the app to include 'test'
    rename_response = await update_application(
        client,
        test_app["id"],
        test_app["etag"],
        {"name": "my-app-test"}
    )
    assert rename_response.status_code == 200
    renamed_app = rename_response.json()
    
    # Try to activate without force flag
    activate_response = await update_application(
        client,
        test_app["id"],
        renamed_app["etag"],
        {"is_active": True}
    )
    assert activate_response.status_code == 422
    assert activate_response.json()["detail"]["code"] == "NAME_FORBIDS_ACTIVATION"
    
    # Try to activate with force flag
    force_response = await update_application(
        client,
        test_app["id"],
        renamed_app["etag"],
        {"is_active": True},
        force=True
    )
    
    assert force_response.status_code in (200, 202)
    
    if force_response.status_code == 202:
        # Handle eventual consistency
        activated = await wait_for_activation_state(
            client,
            test_app["id"],
            True
        )
        assert activated, "Application did not activate within timeout"
    else:
        assert force_response.json()["is_active"] is True

@pytest.mark.asyncio
@pytest.mark.timeout(TEST_TIMEOUTS['test_function'])
async def test_atomic_updates(
    initialized_client: AsyncGenerator[httpx.AsyncClient, None],
    generate_idempotency_key
):
    """
    Test that updates are atomic - all changes succeed or none do.
    """
    client = await anext(initialized_client)
    # Create test application with unique name
    test_id = str(uuid.uuid4())[:8]
    response = await client.post(
        "/applications",
        json={
            "name": f"atomic-test-{test_id}",
            "description": "Base test application"
        },
        headers={"Idempotency-Key": str(uuid.uuid4())}
    )
    assert response.status_code == 201, f"Failed to create test app: {response.text}"
    test_app = response.json()
    # First create another app to create a name conflict
    conflict_name = "conflict-app"
    _, conflict_app = await create_test_application(
        client,
        conflict_name,
        "App for conflict testing",
        generate_idempotency_key()
    )
    
    # Try to update both name (to conflicting) and description
    response = await update_application(
        client,
        test_app["id"],
        test_app["etag"],
        {
            "name": conflict_name,
            "description": "Should not update"
        }
    )
    
    assert response.status_code == 409, (
        "Expected 409 Conflict for name collision"
    )
    
    # Verify no partial update occurred
    current_state = await verify_application_state(
        client,
        test_app["id"],
        {
            "name": test_app["name"],
            "description": test_app["description"]
        }
    )
    assert current_state, "Atomic update check failed - partial update detected"