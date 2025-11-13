# Tech Agent API Refactoring Documentation

## Overview

This document describes the refactoring of the `/v1/tech_agent` endpoint from the monolithic `main.py` to a layered AOCC FastAPI architecture within `api_structure/`.

## Architecture

### Directory Structure

```
api_structure/
├── main.py                           # Application entry point
├── core/                             # Core utilities
│   ├── config.py                     # Configuration management
│   ├── logger.py                     # Logging utilities
│   ├── timer.py                      # @timed decorator for tracing
│   ├── middleware.py                 # Request logging middleware
│   └── exception_handlers.py        # Error handling
├── src/
│   ├── models/
│   │   └── tech_agent_models.py     # Pydantic models for I/O
│   ├── handlers/
│   │   └── tech_agent_handler.py    # Business logic handler
│   ├── pipelines/
│   │   └── tech_agent_pipeline.py   # Orchestration layer
│   ├── routers/
│   │   └── tech_agent_router.py     # FastAPI endpoint
│   └── clients/
│       ├── gpt.py                    # GPT client
│       └── aiohttp_client.py         # HTTP client
```

### Layered Architecture

Following AOCC FastAPI standards:

```
Client Request
    ↓
Router (tech_agent_router.py)
    ↓
Pipeline (tech_agent_pipeline.py)
    ↓
Handler (tech_agent_handler.py)
    ↓
Services/Clients (gpt, aiohttp, cosmos)
```

## Implementation Details

### 1. Models (`tech_agent_models.py`)

Pydantic models for type-safe data validation:

- **TechAgentInput**: Request payload validation
- **TechAgentOutput**: Response data structure
- **TechAgentResponse**: API response wrapper
- **CosmosLogData**: Logging data structure

### 2. Handler (`tech_agent_handler.py`)

Core business logic with the `@timed` decorator for OpenTelemetry tracing.

**Key Methods:**
- `run()`: Main entry point (decorated with @timed)
- `_initialize_chat()`: Setup chat session
- `_process_history()`: Process conversation history
- `_get_user_and_scope_info()`: Extract user info and product scope
- `_search_knowledge_base()`: Query KB for relevant FAQs
- `_generate_response()`: Orchestrate response generation
- `_handle_no_product_line()`: Handle missing product line
- `_handle_high_similarity()`: Handle high KB match
- `_handle_low_similarity()`: Handle low KB match

### 3. Pipeline (`tech_agent_pipeline.py`)

Orchestration layer that:
- Instantiates handler with injected dependencies
- Executes the processing flow
- Returns final result

### 4. Router (`tech_agent_router.py`)

FastAPI endpoint definition:
- Route: `POST /v1/tech_agent`
- Accesses clients via `request.app.state`
- Passes dependencies to pipeline

### 5. Main Application (`main.py`)

Application lifecycle management:
- **Lifespan**: Initialize/close clients (GPT, HTTP, Cosmos)
- **Middleware**: Request logging, CORS, exception handling
- **Router Registration**: Includes tech_agent_router

## Stubbed Dependencies

The following external dependencies are stubbed with mock data:

### Cosmos DB
```python
# TODO: Enable when environment ready
# await cosmos_client.insert_data(cosmos_data)
# Stubbed with mock data
```

Operations stubbed:
- `create_GPT_messages()`: Returns mock conversation history
- `get_latest_hint()`: Returns None
- `get_language_by_websitecode_dev()`: Returns language mapping
- `insert_data()`: Logs instead of inserting
- `insert_hint_data()`: Logs instead of inserting

### Redis
```python
# TODO: Enable when environment ready
# result = await redis_client.get_productline(...)
# Stubbed with mock data
```

Operations stubbed:
- `get_productline()`: Returns product line from mapping
- `get_hint_similarity()`: Returns mock similarity result

### Service Discriminator
```python
# TODO: Enable when environment ready
# response = await service_discriminator.discriminate(...)
# Stubbed with predefined FAQ results
```

Returns:
- Mock FAQ list: `["1043959"]`
- Mock similarity scores: `[0.75]`
- Mock product lines: `["notebook"]`

### Sentence Grouping
```python
# TODO: Enable when environment ready
# result = await sentence_group_classification(...)
# Stubbed with simple grouping
```

### GPT Avatar Generation
```python
# Currently returns static response:
# "嗨！我是華碩智能助手，很高興為您服務！"
# Can be connected to real GPT when credentials are available
```

## Request Flow Example

### Input
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

### Processing Steps

1. **Router receives request** → Validates input against TechAgentInput model
2. **Pipeline created** → Injects GPT and HTTP clients
3. **Handler.run() executed**:
   - Initialize chat session (stubbed history)
   - Process history (stubbed grouping)
   - Start avatar generation (async task)
   - Get user info (stubbed extraction)
   - Determine bot scope (empty product_line → None)
   - Search KB (stubbed FAQ results)
   - Process KB results (low similarity)
   - Generate response based on conditions
   - Log to Cosmos (stubbed)

4. **Response returned** → Formatted according to TechAgentFinalResponse

### Output (No Product Line Case)
```json
{
    "status": 200,
    "message": "OK",
    "result": [
        {
            "renderId": "uuid-here",
            "stream": false,
            "type": "avatarAskProductLine",
            "message": "嗨！我是華碩智能助手，很高興為您服務！",
            "remark": [],
            "option": [
                {
                    "name": "筆記型電腦",
                    "value": "notebook",
                    "icon": "💻"
                },
                {
                    "name": "桌上型電腦",
                    "value": "desktop",
                    "icon": "🖥️"
                }
            ]
        }
    ]
}
```

## Response Types

The handler generates different responses based on conditions:

### 1. No Product Line (`type: "avatarAskProductLine"`)
**Condition**: `product_line` is empty or None

**Response**: Product line selection options

### 2. High Similarity (`type: "avatarTechnicalSupport"`)
**Condition**: `top1_kb_sim > 0.87`

**Response**: Technical support answer with FAQ card

### 3. Low Similarity (`type: "avatarText"` + `type: "avatarAsk"`)
**Condition**: `top1_kb_sim <= 0.87`

**Response**: Handoff message with clarification options

## Testing

### Running Tests

```bash
# Test api_structure version
python -m pytest tests/test_tech_agent_api_structure.py -v

# Test integration (uses api_structure)
python -m pytest tests/test_tech_agent_integration.py -v
```

### Test Coverage

1. **Basic flow test**: Validates response structure and status codes
2. **Product line test**: Tests with pre-specified product line
3. **Input validation test**: Tests Pydantic validation

All tests use stubbed credentials:
```python
os.environ["MYAPP_GPT4O_API_KEY"] = "stub_key_for_testing"
os.environ["MYAPP_GPT4O_RESOURCE_ENDPOINT"] = "https://stub.openai.azure.com/"
os.environ["MYAPP_GPT4O_INTENTDETECT"] = "gpt-4"
```

## Running the Server

### Development Mode

```bash
# From project root
cd /path/to/gina_tech_test2

# Set stub credentials
export MYAPP_GPT4O_API_KEY="stub_key"
export MYAPP_GPT4O_RESOURCE_ENDPOINT="https://stub.openai.azure.com/"
export MYAPP_GPT4O_INTENTDETECT="gpt-4"

# Run api_structure version
python -m api_structure.main
```

### Testing the Endpoint

```bash
curl -X POST http://127.0.0.1:8000/v1/tech_agent \
  -H "Content-Type: application/json" \
  -d '{
    "cus_id": "GINA_TEST",
    "session_id": "test-session-001",
    "chat_id": "test-chat-001",
    "user_input": "我的筆電卡在登入畫面，完全沒有反應。",
    "websitecode": "tw",
    "product_line": "",
    "system_code": "rog"
  }'
```

## Enabling Real Services

To connect real services, uncomment and configure:

### 1. Cosmos DB

In `api_structure/main.py`:
```python
# Uncomment in lifespan:
# cosmos_client = CosmosDbClient()
# await cosmos_client.initialize()
# app.state.cosmos_client = cosmos_client

# And in shutdown:
# await app.state.cosmos_client.close()
```

In `tech_agent_handler.py`:
```python
# Uncomment all Cosmos operations:
# messages, last_hint, lang = await asyncio.gather(
#     cosmos_settings.create_GPT_messages(...),
#     cosmos_settings.get_latest_hint(...),
#     cosmos_settings.get_language_by_websitecode_dev(...)
# )
```

### 2. Redis

Configure Redis connection and uncomment:
```python
# result = await redis_client.get_productline(...)
```

### 3. Service Discriminator

Configure and uncomment:
```python
# response = await service_discriminator.discriminate(...)
```

## Key Differences from Original

| Aspect | Original (`main.py`) | Refactored (`api_structure/`) |
|--------|---------------------|-------------------------------|
| Structure | Monolithic processor | Layered (Router→Pipeline→Handler) |
| Dependencies | DependencyContainer | Injected via app.state |
| Client Init | Custom lifespan | Standardized client pattern |
| Error Handling | Mixed | Centralized exception handlers |
| Tracing | Partial | @timed on all handlers |
| Testing | Requires all deps | Stubbed for independence |
| Type Safety | Basic Pydantic | Comprehensive models |

## Compliance with AOCC Standards

✅ **Layered Architecture**: Router → Pipeline → Handler → Services
✅ **Client Management**: Initialize/close in lifespan, access via app.state
✅ **OpenTelemetry**: @timed decorator on handlers
✅ **Error Handling**: AbortException, WarningException patterns ready
✅ **Logging**: Uses set_extract_log() pattern (via middleware)
✅ **Type Safety**: Pydantic models throughout
✅ **Naming Conventions**: snake_case functions, PascalCase classes

## Future Improvements

1. **Connect real GPT**: Use actual GPT client for avatar responses
2. **Restore Cosmos**: Enable database logging and history retrieval
3. **Add Redis**: Enable caching and product line lookup
4. **Service Integration**: Connect to real service discriminator
5. **Streaming Support**: Implement SSE streaming endpoint
6. **Error Recovery**: Add retry logic for external services
7. **Metrics**: Add Prometheus metrics collection
8. **Rate Limiting**: Add request throttling

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   ```
   ValueError: GPT-4 client requires MYAPP_GPT4O_API_KEY...
   ```
   **Solution**: Set stub credentials or real API keys

2. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'api_structure'
   ```
   **Solution**: Run from project root: `python -m api_structure.main`

3. **Port Already in Use**
   ```
   OSError: [Errno 98] Address already in use
   ```
   **Solution**: Kill existing process or use different port

## Conclusion

The refactored `/v1/tech_agent` endpoint now follows AOCC FastAPI standards while maintaining functional compatibility with the original implementation. All external dependencies are properly stubbed to allow independent testing and development.
