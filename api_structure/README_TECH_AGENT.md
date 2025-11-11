# Tech Agent API - Refactored Structure

## Overview

This document describes the refactored `/v1/tech_agent` API endpoint in the `api_structure/` directory, following AOCC FastAPI architectural standards.

## Architecture

The refactored code follows a strict layered architecture:

```
Clients → Routers → Pipelines → Handlers → Core
```

### Directory Structure

```
api_structure/
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   └── tech_agent_models.py          # Pydantic request/response schemas
│   ├── handlers/
│   │   └── tech_agent_handler.py         # Business logic
│   ├── pipelines/
│   │   └── tech_agent_pipeline.py        # Orchestration layer
│   └── routers/
│       └── tech_agent_router.py          # FastAPI endpoint
├── core/
│   ├── config.py                          # Configuration
│   ├── logger.py                          # Logging utilities
│   ├── timer.py                           # OpenTelemetry decorators
│   ├── middleware.py                      # Request logging middleware
│   └── exception_handlers.py             # Exception handlers
└── main.py                                # FastAPI app with router registration
```

## API Endpoint

### POST /v1/tech_agent

Technical support agent endpoint that processes user queries and returns appropriate responses.

#### Request Body

```json
{
  "cus_id": "GINA_TEST",
  "session_id": "f6b3ddd8-6c55-4edc-9cf0-8408664cb89d",
  "chat_id": "c516e816-0ad1-44f1-9046-7878bd78b3bc",
  "user_input": "我的筆電卡在登入畫面，完全沒有反應。",
  "websitecode": "tw",
  "product_line": "",
  "system_code": "rog"
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| cus_id | string | Yes | Customer ID |
| session_id | string | Yes | Session ID for tracking |
| chat_id | string | Yes | Chat conversation ID |
| user_input | string | Yes | User's input message |
| websitecode | string | Yes | Website code (e.g., "tw", "us") |
| product_line | string | No | Product line (empty if unknown) |
| system_code | string | Yes | System code (e.g., "rog", "asus") |

#### Response Format

```json
{
  "status": 200,
  "message": "OK",
  "result": [
    {
      "renderId": "a19afe13-8082-4695-b06b-33e832b9009b",
      "stream": false,
      "type": "avatarAskProductLine",
      "message": "我理解您遇到了技術問題。請問是哪個產品線的問題呢？",
      "remark": [],
      "option": [
        {
          "name": "筆記型電腦",
          "value": "notebook",
          "icon": "laptop"
        },
        {
          "name": "桌上型電腦",
          "value": "desktop",
          "icon": "desktop"
        }
      ]
    }
  ]
}
```

#### Response Types

The API can return different response types based on the processing logic:

1. **avatarAskProductLine** - Asks user to select a product line
2. **avatarTechnicalSupport** - Provides technical support answer with FAQ cards
3. **avatarText** + **avatarAsk** - Low similarity handoff to human agent

## Running the API

### Development Mode (with test stubs)

```bash
# Set test mode to use mock data
export TESTING=true

# Run the server
python -m api_structure.main
```

The server will start on `http://127.0.0.1:8000`

### Testing

Run the integration test:

```bash
# Run with test environment
TESTING=true python -m pytest tests/test_tech_agent_api_structure.py -v
```

### Production Mode

When deploying to production, ensure all required environment variables are set:

- `MYAPP_GPT4O_API_KEY`
- `MYAPP_GPT4O_RESOURCE_ENDPOINT`
- `MYAPP_GPT4O_INTENTDETECT`
- `MYAPP_CONNECTION_STRING` (for Azure Application Insights)

## Code Components

### 1. Models Layer (`src/models/tech_agent_models.py`)

Defines Pydantic models for:
- `TechAgentInput` - Request payload
- `TechAgentOutput` - Processing output
- `TechAgentResponse` - API response
- `RenderItem`, `KBInfo`, etc. - Supporting models

### 2. Handler Layer (`src/handlers/tech_agent_handler.py`)

**Class**: `TechAgentHandler`

Contains the main business logic with methods:
- `run()` - Main entry point (decorated with @timed)
- `_initialize_chat()` - Initialize chat session
- `_get_user_info()` - Extract user information
- `_get_bot_scope()` - Determine product line scope
- `_search_knowledge_base()` - Search KB for solutions
- `_handle_no_product_line()` - Handle missing product line
- `_handle_high_similarity()` - Handle KB match
- `_handle_low_similarity()` - Handle low confidence

**Key Features**:
- All external API calls are stubbed with TODO comments
- Mock data returns for testing
- Original logic preserved in comments
- Proper error handling and logging

### 3. Pipeline Layer (`src/pipelines/tech_agent_pipeline.py`)

**Class**: `TechAgentPipeline`

Orchestrates the handler execution:
```python
async def run(user_input: TechAgentInput) -> Dict[str, Any]:
    # Execute handler and return result
```

### 4. Router Layer (`src/routers/tech_agent_router.py`)

FastAPI router that defines the endpoint:
```python
@router.post("/v1/tech_agent")
async def tech_agent_endpoint(
    user_input: TechAgentInput,
    request: Request,
) -> Dict[str, Any]:
    # Create pipeline and execute
```

## Stubbed Dependencies

All external dependencies are stubbed for testing:

### Cosmos DB Operations
```python
# TODO: Enable when environment ready
# cosmos_data = { ... }
# await cosmos_settings.insert_data(cosmos_data)
```

### Redis/API Calls
```python
# TODO: Enable when environment ready
# response = await service_discriminator.service_discreminator_with_productline(...)
# Mock response
faq_result = {"faq": ["1049123"], "cosineSimilarity": [0.75]}
```

### GPT Calls
```python
# TODO: Enable when environment ready
# avatar_response = await service.reply_with_faq_gemini_sys_avatar(...)
# Mock avatar message
avatar_message = "我理解您遇到了技術問題。請問是哪個產品線的問題呢？"
```

## Configuration

### Test Mode

Set `TESTING=true` environment variable to:
- Skip client initialization that requires credentials
- Use mock data instead of external services

### Logging

Uses the `get_logger()` function from `api_structure.core.logger`:
```python
logger = get_logger(__name__)
logger.info("Processing request...")
```

### Tracing

All handlers use the `@timed` decorator for OpenTelemetry tracing:
```python
@timed(task_name="tech_agent_handler_process")
async def run(self, user_input: TechAgentInput) -> Dict[str, Any]:
    # Handler logic
```

## Compliance

### AOCC FastAPI Standards ✅
- Layered architecture (clients → routers → pipelines → handlers)
- `@timed` decorator for tracing
- Dependency injection via `app.state`
- Error handling with custom exception handlers
- Request logging middleware

### Python Coding Standards ✅
- PEP 8 compliant (verified with flake8)
- Type hints throughout
- Docstrings for all public functions
- Formatted with black (88 char line length)
- Imports organized with isort

## Migration Notes

### Differences from Original main.py

1. **Simplified Dependencies**: The refactored version doesn't require the complex `DependencyContainer` from original code. It uses mock data instead.

2. **Stubbed External Services**: All external services (Cosmos, Redis, GPT) are stubbed with clear TODO comments marking where to re-enable.

3. **Test-Friendly**: Can run without actual credentials by setting `TESTING=true`.

4. **Cleaner Separation**: Clear separation of concerns with distinct layers.

### Re-enabling External Services

To re-enable external services, search for "TODO: Enable when environment ready" comments and:
1. Uncomment the real implementation
2. Remove or comment out the mock data
3. Ensure environment variables are set
4. Test thoroughly

## Troubleshooting

### Import Errors
- Ensure you're in the project root directory
- Check Python path includes the project root

### Missing Dependencies
```bash
pip install -r requirements.txt
pip install azure-monitor-opentelemetry opentelemetry-instrumentation-fastapi apscheduler
```

### Test Failures
- Ensure `TESTING=true` is set
- Check logs for specific error messages
- Verify all required files are present

## Future Enhancements

Potential improvements:
1. Add streaming response support (commented code exists in original)
2. Implement follow-up question handling
3. Add more comprehensive test coverage
4. Add rate limiting
5. Implement caching for frequently asked questions
