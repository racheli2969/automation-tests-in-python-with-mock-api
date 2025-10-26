# Mock API Testing Project

This project implements a mock API service with comprehensive test coverage for idempotent creation and optimistic locking scenarios.

## Project Structure

```
.
├── mock_api/                  # Main API implementation package
│   ├── api/                   # API routes and handlers
│   │   └── applications.py    # Application endpoints implementation
│   ├── config/                # Configuration settings
│   │   └── settings.py        # API configuration and environment variables
│   ├── models/                # Data models
│   │   └── application.py     # Application model definition
│   ├── services/              # Business logic layer
# Mock API Testing Project

This project implements a mock API service with comprehensive test coverage for idempotent creation and optimistic locking scenarios.

## Project Structure

```
.
├── mock_api/                  # Main API implementation package
│   ├── api/                   # API routes and handlers
│   │   └── applications.py    # Application endpoints implementation
│   ├── config/                # Configuration settings
│   │   └── settings.py        # API configuration and environment variables
│   ├── models/                # Data models
│   │   └── application.py     # Application model definition
│   ├── services/             # Business logic layer
│   │   └── application_service.py # Application business logic
│   ├── __init__.py           # Package initialization
│   └── app.py               # FastAPI application setup
├── tests/                    # Test suite
│   ├── conftest.py          # Shared test fixtures and configurations
│   ├── test_idempotent_create.py    # Tests for POST endpoint and idempotency
│   │   # - Concurrent requests with same idempotency key
│   │   # - Rate limiting with retry mechanism
│   │   # - Negative idempotency tests
│   ├── test_patch_optimistic_locking.py  # Tests for PATCH endpoint
│   │   # - Name normalization and uniqueness
│   │   # - Optimistic locking with ETag
│   │   # - Activation rules and force flag
│   │   # - Atomic updates
│   ├── helpers/             # Test helper modules
│   │   ├── __init__.py     # Package initialization
│   │   ├── application_helpers.py  # Application-specific test helpers
│   │   │   # - create_application()
│   │   │   # - update_application()
│   │   │   # - verify_application_state()
│   │   │   # - wait_for_activation_state()
│   │   └── test_helpers.py  # Generic test utilities
│   │       # - make_concurrent_requests()
│   └── __init__.py
├── pyproject.toml             # Project metadata and tool configuration
├── requirements.txt           # Project dependencies
└── README.md                  # Project documentation
```

## Setup Instructions

1. Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

## Running the Mock API

The mock API can be started using uvicorn:

```powershell
uvicorn mock_api.app:app --host 127.0.0.1 --port 8000
```

## Running Tests

To run all tests:
```powershell
pytest tests/
```

To run tests with parallel execution:
```powershell
pytest tests/ -n auto
```

To run a specific test file:
```powershell
pytest tests/test_idempotent_create.py
pytest tests/test_patch_optimistic_locking.py
```

To see detailed logs during test execution:
```powershell
# Show logs for all levels (DEBUG, INFO, WARNING, ERROR)
pytest tests/ -v --log-cli-level=INFO

# Show logs only for failed tests
pytest tests/ --log-cli-level=INFO --log-cli-format="%(asctime)s %(message)s" -v --showlocals
```

## Requirements

- Python 3.8 or higher

## Configuration

The mock API supports two environment variables for controlling activation behavior:

- `ACTIVATION_MODE`: Set to either "immediate" or "eventual" (default: "immediate")
- `ACTIVATION_DELAY_MS`: Delay in milliseconds for eventual activation (default: 1500)

Example of running with eventual consistency:
```powershell
$env:ACTIVATION_MODE="eventual"; $env:ACTIVATION_DELAY_MS="1500"; uvicorn mock_api.app:app
```

## Implementation Details

### Mock API Features
- In-memory storage for applications and idempotency records
- Rate limiting (5 requests per minute per token)
- Idempotent POST endpoint with conflict detection
- PATCH endpoint with optimistic locking
- Configurable activation modes (immediate/eventual)
- Proper error handling and status codes

### Test Coverage
1. Idempotent Create Test:
   - Concurrent requests with same idempotency key
   - Rate limit handling with retry
   - Idempotency with different payloads

2. Optimistic Locking Test:
   - Name normalization and uniqueness
   - Concurrent update handling
   - Activation rules and force flag
   - Eventual consistency handling
   - Atomic updates

## Design Choices

1. **FastAPI Framework**: Chosen for its async support, automatic OpenAPI documentation, and built-in request validation.

2. **In-Memory Storage**: Simple dictionary-based storage suitable for testing purposes while maintaining proper isolation between test runs.

3. **Async Testing**: Using pytest-asyncio for proper handling of asynchronous operations and concurrent requests.

4. **Fixtures**: Modular test fixtures for clean setup/teardown and reusable components.

5. **Helper Functions**: Utilities like `retry_until` and `respect_retry_after` for better test reliability.

6. **Idempotency Implementation**: Token-scoped idempotency records to prevent cross-token conflicts.

7. **Rate Limiting**: Simple rolling window implementation with cleanup of old records.

8. **Error Handling**: Detailed error responses with appropriate status codes and headers.
```

## Setup Instructions

1. Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

## Running the Mock API

The mock API can be started using uvicorn:

```powershell
uvicorn mock_api.app:app --host 127.0.0.1 --port 8000
```

## Running Tests

To run all tests:
```powershell
pytest tests/
```

To run tests with parallel execution:
```powershell
pytest tests/ -n auto
```

To run a specific test file:
```powershell
pytest tests/test_idempotent_create.py
pytest tests/test_patch_optimistic_locking.py
```

To see detailed logs during test execution:
```powershell
# Show logs for all levels (DEBUG, INFO, WARNING, ERROR)
pytest tests/ -v --log-cli-level=INFO

# Show logs only for failed tests
pytest tests/ --log-cli-level=INFO --log-cli-format="%(asctime)s %(message)s" -v --showlocals
```

## Requirements

- Python 3.8 or higher

## Configuration

The mock API supports two environment variables for controlling activation behavior:

- `ACTIVATION_MODE`: Set to either "immediate" or "eventual" (default: "immediate")
- `ACTIVATION_DELAY_MS`: Delay in milliseconds for eventual activation (default: 1500)

Example of running with eventual consistency:
```powershell
$env:ACTIVATION_MODE="eventual"; $env:ACTIVATION_DELAY_MS="1500"; uvicorn mock_api.app:app
```

## Implementation Details

### Mock API Features
- In-memory storage for applications and idempotency records
- Rate limiting (5 requests per minute per token)
- Idempotent POST endpoint with conflict detection
- PATCH endpoint with optimistic locking
- Configurable activation modes (immediate/eventual)
- Proper error handling and status codes

### Test Coverage
1. Idempotent Create Test:
   - Concurrent requests with same idempotency key
   - Rate limit handling with retry
   - Idempotency with different payloads

2. Optimistic Locking Test:
   - Name normalization and uniqueness
   - Concurrent update handling
   - Activation rules and force flag
   - Eventual consistency handling
   - Atomic updates

## Design Choices

1. **FastAPI Framework**: Chosen for its async support, automatic OpenAPI documentation, and built-in request validation.

2. **In-Memory Storage**: Simple dictionary-based storage suitable for testing purposes while maintaining proper isolation between test runs.

3. **Async Testing**: Using pytest-asyncio for proper handling of asynchronous operations and concurrent requests.

4. **Fixtures**: Modular test fixtures for clean setup/teardown and reusable components.

5. **Helper Functions**: Utilities like `retry_until` and `respect_retry_after` for better test reliability.

6. **Idempotency Implementation**: Token-scoped idempotency records to prevent cross-token conflicts.

7. **Rate Limiting**: Simple rolling window implementation with cleanup of old records.

8. **Error Handling**: Detailed error responses with appropriate status codes and headers.