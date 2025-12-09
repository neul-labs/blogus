# Test Coverage Report

## Summary

| Metric | Value |
|--------|-------|
| **Total Coverage** | 47% |
| **Total Tests** | 182 |
| **Passed** | 182 |
| **Skipped** | 2 (FastAPI tests when not installed) |

## Coverage by Area

### Well-Covered Areas (>70%)

| Module | Coverage | Notes |
|--------|----------|-------|
| `application/dto.py` | 100% | Data transfer objects |
| `domain/models/registry.py` | 85% | Registry domain models |
| `domain/services/prompt_parser.py` | 85% | Prompt file parsing |
| `domain/services/prompt_analyzer.py` | 82% | Prompt analysis service |
| `infrastructure/config/settings.py` | 81% | Configuration management |
| `domain/models/prompt.py` | 79% | Core prompt models |
| `infrastructure/llm/litellm_provider.py` | 77% | LLM provider implementation |
| `domain/services/version_engine.py` | 75% | Git-based versioning |
| `domain/models/analysis.py` | 77% | Analysis models |
| `domain/models/comparison.py` | 72% | Comparison models |
| `domain/models/testing.py` | 72% | Testing models |
| `domain/models/execution.py` | 71% | Execution models |

### Moderate Coverage (40-70%)

| Module | Coverage | Notes |
|--------|----------|-------|
| `infrastructure/container.py` | 66% | DI container - missing database backend tests |
| `infrastructure/git/repo.py` | 61% | Git operations - some edge cases untested |
| `domain/services/detection_engine.py` | 60% | Codebase scanning - complex report generation untested |
| `infrastructure/storage/file_repositories.py` | 54% | File storage - search and filter methods need more tests |
| `application/services/prompt_service.py` | 46% | Prompt service - analysis and comparison methods untested |
| `interfaces/web/container.py` | 43% | Web container - service creation untested |
| `interfaces/cli/commands/scan.py` | 40% | Scan command - verbose output and fix command untested |

### Low Coverage Areas (<40%)

These areas need additional testing effort:

#### Web Interface (0-2%)

| Module | Coverage | Reason |
|--------|----------|--------|
| `interfaces/web/main.py` | 2% | FastAPI app setup - needs integration tests |
| `interfaces/web/routers/prompts.py` | 0% | Prompt API endpoints - needs mock service injection |
| `interfaces/web/routers/registry.py` | 0% | Registry API endpoints - needs mock service injection |
| `interfaces/web/routers/prompt_files.py` | 0% | Prompt file API - needs mock service injection |

**Why untested:**
- Web routers require full FastAPI test client setup with dependency injection
- Need to mock database/file repositories
- Many endpoints have complex request/response handling

**Recommended approach:**
```python
# Example test pattern for web routers
from fastapi.testclient import TestClient
from blogus.interfaces.web.main import app
from blogus.interfaces.web.container import get_container

def test_endpoint():
    mock_container = create_mock_container()
    app.dependency_overrides[get_container] = lambda: mock_container

    client = TestClient(app)
    response = client.get("/api/v1/prompts")

    assert response.status_code == 200
```

#### CLI Commands (18-33%)

| Module | Coverage | Reason |
|--------|----------|--------|
| `interfaces/cli/commands/exec.py` | 18% | Execute command - multi-model execution untested |
| `interfaces/cli/commands/analyze.py` | 27% | Analyze command - LLM analysis flow untested |
| `interfaces/cli/commands/registry.py` | 28% | Registry commands - deployment management untested |
| `interfaces/cli/commands/prompts.py` | 33% | Prompts commands - edit/delete/show untested |

**Why untested:**
- Commands require complex CLI runner setup with isolated filesystems
- Many commands interact with LLM APIs (need mocking)
- Some commands have interactive prompts

**Recommended approach:**
```python
from click.testing import CliRunner
from unittest.mock import patch

def test_analyze_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Setup test environment
        with patch('blogus.interfaces.cli.commands.analyze.get_llm_provider') as mock:
            mock.return_value.analyze_prompt.return_value = mock_result
            result = runner.invoke(analyze_command, ['--prompt', 'test.prompt'])
            assert result.exit_code == 0
```

#### Application Services (35-46%)

| Module | Coverage | Reason |
|--------|----------|--------|
| `application/services/registry_service.py` | 35% | Registry service - execution/metrics/rollback untested |
| `application/services/prompt_service.py` | 46% | Prompt service - analysis/comparison/testing untested |

**Why untested:**
- Services have many async methods requiring proper async test setup
- Heavy LLM integration requires extensive mocking
- Complex business logic with many edge cases

**Recommended approach:**
```python
@pytest.mark.asyncio
async def test_execute_deployment():
    mock_registry = AsyncMock()
    mock_metrics = AsyncMock()
    mock_llm = AsyncMock()

    service = RegistryService(mock_registry, mock_metrics, mock_llm)

    result = await service.execute_deployment(request)

    assert result.success is True
    mock_llm.generate_response.assert_called_once()
```

#### Infrastructure (19-31%)

| Module | Coverage | Reason |
|--------|----------|--------|
| `infrastructure/database/repositories.py` | 19% | Database repos - need Tortoise ORM setup |
| `infrastructure/parsers/python_parser.py` | 24% | Python parsing - complex AST traversal |
| `infrastructure/parsers/js_parser.py` | 31% | JS parsing - regex-based detection |
| `infrastructure/observability/tracing.py` | 27% | Tracing - OpenTelemetry integration |
| `infrastructure/observability/instrumented_service.py` | 18% | Instrumented service - tracing spans |
| `domain/services/comparison_engine.py` | 26% | Comparison - embedding service needs mock |

**Why untested:**
- Database tests require actual database connection or in-memory SQLite
- Parser tests need many code samples to cover edge cases
- Observability requires OpenTelemetry SDK mocking

## Priority Testing Recommendations

### High Priority (Business Critical)

1. **Registry Service Execution** (`registry_service.py`)
   - `execute_deployment()` - Core prompt execution
   - `rollback_deployment()` - Safety feature
   - Traffic routing logic

2. **Web API Endpoints** (`routers/`)
   - POST `/api/v1/prompts/execute` - Main execution endpoint
   - POST `/api/v1/registry/deployments` - Deployment management

3. **CLI Execute Command** (`exec.py`)
   - Single model execution
   - Multi-model comparison

### Medium Priority (Quality)

4. **Prompt Service Analysis** (`prompt_service.py`)
   - `analyze_prompt()` - Prompt quality analysis
   - `compare_outputs()` - Model comparison

5. **Detection Engine** (`detection_engine.py`)
   - `add_markers()` - Code modification
   - Report generation formats

6. **Database Repositories** (`database/repositories.py`)
   - CRUD operations with actual database

### Lower Priority (Edge Cases)

7. **Parsers** (`python_parser.py`, `js_parser.py`)
   - Edge cases in code detection
   - Various API call patterns

8. **Observability** (`tracing.py`, `instrumented_service.py`)
   - OpenTelemetry span creation
   - Metric recording

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=blogus --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_cli.py -v

# Run tests matching pattern
uv run pytest -k "test_execute" -v
```

## Test Files Structure

```
tests/
├── test_application.py      # Application service tests
├── test_cli.py              # CLI command tests
├── test_container.py        # DI container tests
├── test_detection_engine.py # Codebase scanning tests
├── test_domain.py           # Domain model tests
├── test_domain_services.py  # Domain service tests
├── test_infrastructure.py   # Infrastructure tests
├── test_interfaces.py       # Interface tests (FastAPI)
├── test_llm_provider.py     # LLM provider tests
├── test_prompt_files.py     # Prompt file parsing tests
├── test_registry.py         # Registry model tests
├── test_registry_service.py # Registry service tests
├── test_version_engine.py   # Git versioning tests
├── test_web_api.py          # Web API endpoint tests
└── COVERAGE.md              # This file
```
