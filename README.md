# Mock API Testing Project

This project implements a mock API service with comprehensive test coverage for idempotent creation and optimistic locking scenarios. It is designed to demonstrate robust testing practices and API behavior under various conditions.

## Project Overview

This project includes:
- A mock API built with FastAPI.
- In-memory storage for applications and idempotency records.
- Comprehensive test coverage for concurrency, rate limiting, optimistic locking, and activation rules.

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

1. **Create and activate a virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate
   ```

2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Verify installation:**
   Ensure all dependencies are installed correctly by running:
   ```powershell
   pytest --version
   ```

## Running the Mock API

The mock API can be started using uvicorn:

```powershell
uvicorn mock_api.app:app --host 127.0.0.1 --port 8000
```

Once started, the API will be accessible at `http://127.0.0.1:8000`.

## Running Tests

To ensure the API behaves as expected, run the test suite:

- **Run all tests:**
  ```powershell
  pytest tests/
  ```

- **Run tests with parallel execution:**
  ```powershell
  pytest tests/ -n auto
  ```

- **Run a specific test file:**
  ```powershell
  pytest tests/test_idempotent_create.py
  pytest tests/test_patch_optimistic_locking.py
  ```

- **View detailed logs during test execution:**
  ```powershell
  pytest tests/ -v --log-cli-level=INFO
  ```

## Requirements

- Python 3.8 or higher

## Configuration

The mock API supports the following environment variables for controlling activation behavior:

- `ACTIVATION_MODE`: Set to either "immediate" or "eventual" (default: "immediate").
- `ACTIVATION_DELAY_MS`: Delay in milliseconds for eventual activation (default: 1500).

Example of running with eventual consistency:
```powershell
$env:ACTIVATION_MODE="eventual"; $env:ACTIVATION_DELAY_MS="1500"; uvicorn mock_api.app:app
```

## Implementation Details

### Mock API Features
- **Idempotent POST Endpoint:** Ensures no duplicate resources are created for the same idempotency key.
- **PATCH Endpoint with Optimistic Locking:** Handles concurrent updates with ETag/version control.
- **Rate Limiting:** Limits to 5 requests per minute per token.
- **Configurable Activation Modes:** Supports immediate or eventual activation.
- **Error Handling:** Provides detailed error responses with appropriate status codes.

### Test Coverage Highlights
1. **Idempotent Create Test:**
   - Verifies concurrency handling with the same idempotency key.
   - Tests rate limiting and retry mechanisms.
   - Ensures idempotency even with different payloads.

2. **Optimistic Locking Test:**
   - Validates name normalization and uniqueness.
   - Tests concurrent updates with ETag/version control.
   - Ensures activation rules are enforced, including eventual consistency.
   - Verifies atomicity of updates.

## Design Choices

1. **FastAPI Framework:** Chosen for its async capabilities, automatic OpenAPI documentation, and robust request validation.
2. **In-Memory Storage:** Simplifies testing while maintaining isolation between test runs.
3. **Async Testing:** Utilizes `pytest-asyncio` for handling asynchronous operations.
4. **Fixtures and Helpers:** Modular fixtures and helper functions for clean, reusable test components.
5. **Error Handling:** Provides clear and descriptive error messages for easier debugging.

## Contributing

Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Submit a pull request with a clear description of your changes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.