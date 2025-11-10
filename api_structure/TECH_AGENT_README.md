# Tech Agent Endpoint Refactoring

## Overview

This document describes the refactored `/v1/tech_agent` endpoint that has been migrated from the root `main.py` to the `api_structure/` folder following AOCC FastAPI development standards.

## Architecture

The refactored endpoint follows a layered architecture:

```
Client Request
    ↓
Router (tech_agent_router.py)
    ↓
Pipeline (tech_agent_pipeline.py)
    ↓
Handler (tech_agent_handler.py)
    ↓
Models (tech_agent_models.py)
```

## File Structure

```
api_structure/
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   └── tech_agent_models.py    # Request/Response models
│   ├── handlers/
│   │   └── tech_agent_handler.py   # Business logic
│   ├── pipelines/
│   │   └── tech_agent_pipeline.py  # Orchestration layer
│   └── routers/
│       └── tech_agent_router.py    # FastAPI endpoint
├── core/
│   ├── middleware.py               # Request/response logging
│   └── logger.py                   # Logging utilities
└── main.py                         # App initialization
```

## Components

### 1. Models (`tech_agent_models.py`)

Defines the request and response data structures:

- `TechAgentRequest`: Input model with validation
- `TechAgentResponse`: Response model
- `RenderItem`: Individual render item in response
- `RenderOption`: Options for user selection
- `KnowledgeBase`: KB information

### 2. Handler (`tech_agent_handler.py`)

Contains the business logic:

- `TechAgentHandler.process()`: Main processing method
- `_handle_no_product_line()`: Handles product line selection
- `_handle_with_product_line()`: Handles technical support with KB

All methods are decorated with `@timed` for OpenTelemetry tracing.

### 3. Pipeline (`tech_agent_pipeline.py`)

Orchestrates the request flow:

- Validates input
- Calls handler
- Formats response

### 4. Router (`tech_agent_router.py`)

Defines the FastAPI endpoint:

- POST `/v1/tech_agent`
- Uses Pydantic models for validation
- Returns structured response

## Mock Implementation

Due to permission limitations, all external API and database calls are mocked:

### Scenario 1: No Product Line

**Request:**
```json
{
  "cus_id": "test",
  "session_id": "test-session",
  "chat_id": "test-chat",
  "user_input": "筆電問題",
  "websitecode": "tw",
  "product_line": "",
  "system_code": "rog"
}
```

**Response:**
- Type: `avatarAskProductLine`
- Returns 3 product line options (notebook, desktop, phone)

### Scenario 2: With Product Line

**Request:**
```json
{
  "cus_id": "test",
  "session_id": "test-session",
  "chat_id": "test-chat",
  "user_input": "登入問題",
  "websitecode": "tw",
  "product_line": "notebook",
  "system_code": "rog"
}
```

**Response:**
- Type: `avatarTechnicalSupport`
- Includes FAQ card with mock KB content

## Features

### OpenTelemetry Integration

All handlers use the `@timed` decorator:

```python
@timed(task_name="tech_agent_handler_process")
async def process(self, request: TechAgentRequest) -> Dict[str, Any]:
    # Processing logic
    pass
```

### Logging

Uses `set_extract_log` to enrich logs:

```python
set_extract_log({
    "user_input": request.user_input,
    "session_id": request.session_id,
    "product_line": request.product_line,
})
```

Middleware automatically logs all requests/responses to Cosmos DB.

### Error Handling

Errors are handled by the middleware:
- `AbortException`: For critical errors that stop request processing
- `WarningException`: For recoverable errors

## Testing

### Integration Test

Run the integration test:

```bash
export MYAPP_GPT4O_API_KEY=test
export MYAPP_GPT4O_RESOURCE_ENDPOINT=https://test.com
export MYAPP_GPT4O_INTENTDETECT=test
pytest tests/test_tech_agent_integration.py -v
```

Expected output:
```
tests/test_tech_agent_integration.py::test_tech_agent_basic_flow PASSED
```

### Manual Testing

Test with curl:

```bash
curl -X POST http://localhost:8000/v1/tech_agent \
  -H "Content-Type: application/json" \
  -d '{
    "cus_id": "test",
    "session_id": "test-session",
    "chat_id": "test-chat",
    "user_input": "筆電問題",
    "websitecode": "tw",
    "product_line": "",
    "system_code": "rog"
  }'
```

## Development Guidelines

### Adding New Features

1. Update models if needed (`tech_agent_models.py`)
2. Add business logic in handler (`tech_agent_handler.py`)
3. Update pipeline if orchestration changes (`tech_agent_pipeline.py`)
4. Test with integration tests

### Code Quality

All code must pass:
- `black --line-length 79 <file>`
- `flake8 --max-line-length=79 <file>`
- `isort --profile black --line-length 79 <file>`
- `mypy <file> --ignore-missing-imports`

### Documentation

All public functions must have docstrings following PEP 257:

```python
def function_name(param1: str) -> dict:
    """
    Brief description.

    Detailed description if needed.

    Args:
        param1: Description of param1

    Returns:
        Description of return value
    """
    pass
```

## Migration Notes

### Differences from Original

1. **Structure**: Layered architecture vs. monolithic processor
2. **Tracing**: Uses `@timed` decorator for all handlers
3. **Logging**: Integrated with middleware
4. **Models**: Pydantic models for type safety
5. **Testing**: Simplified test setup

### Backward Compatibility

The old endpoint in root `main.py` remains untouched. Both endpoints can coexist during migration period.

## Future Improvements

When API/DB permissions are available:

1. Replace mock responses in `_handle_no_product_line()`
2. Replace mock responses in `_handle_with_product_line()`
3. Integrate real service calls:
   - `service_discriminator.service_discreminator_with_productline()`
   - `service_process.technical_support_hint_create()`
   - `ts_rag.reply_with_faq_gemini_sys_avatar()`

## References

- AOCC FastAPI Standards: See `api_structure/` examples
- Original Implementation: See `src/core/tech_agent_api.py`
- Testing: See `tests/test_tech_agent_integration.py`
