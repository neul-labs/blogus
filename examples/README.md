# Blogus Examples

This directory contains example usage of Blogus with the clean architecture for various prompt engineering tasks.

## Available Examples

### 1. Basic Usage (`basic_usage.py`)

Demonstrates basic prompt analysis and test generation:

```bash
python examples/basic_usage.py
```

### 2. Basic Analysis (`basic_analysis.py`)

Shows prompt analysis and execution with detailed results:

```bash
python examples/basic_analysis.py
```

### 3. Cross-Model Comparison (`cross_model.py`)

Compares the same prompt across multiple LLM models:

```bash
python examples/cross_model.py
```

### 4. Test Generation (`test_generation.py`)

Generates test cases for parameterized prompts:

```bash
python examples/test_generation.py
```

### 5. Template Management (`template_management.py`)

Demonstrates template creation, rendering, and management:

```bash
python examples/template_management.py
```

## Clean Architecture Usage

All examples use the new clean architecture with proper dependency injection:

```python
import asyncio
from blogus.interfaces.web.container import get_container
from blogus.application.dto import AnalyzePromptRequest

async def main():
    # Get container and services
    container = get_container()
    prompt_service = container.get_prompt_service()

    # Create request
    request = AnalyzePromptRequest(
        prompt_text="Your prompt here",
        judge_model="gpt-4",
        goal="Your goal here"
    )

    # Call service
    response = await prompt_service.analyze_prompt(request)
    print(f"Goal alignment: {response.analysis.goal_alignment}/10")

if __name__ == "__main__":
    asyncio.run(main())
```

## Prerequisites

1. **Environment Variables**: Set up your API keys:
   ```bash
   export OPENAI_API_KEY="your-key-here"
   export ANTHROPIC_API_KEY="your-key-here"
   export GROQ_API_KEY="your-key-here"
   ```

2. **Dependencies**: Install with web extras:
   ```bash
   uv sync --extra web
   ```

## Key Concepts

### Services
- **PromptService**: Analysis, execution, and test generation
- **TemplateService**: Template management and rendering

### DTOs (Data Transfer Objects)
- **AnalyzePromptRequest/Response**: For prompt analysis
- **ExecutePromptRequest/Response**: For prompt execution
- **GenerateTestRequest/Response**: For test case generation
- **CreateTemplateRequest/Response**: For template creation
- **RenderTemplateRequest/Response**: For template rendering

### Container
The `WebContainer` provides dependency injection and service management:
- Manages configuration
- Provides LLM providers
- Handles repositories
- Offers application services

### Template System
Templates use Jinja2-style syntax with double braces:
```
Hello {{name}}, your order {{order_id}} is {{status}}.
```

## Error Handling

All examples include proper error handling for:
- API failures
- Network issues
- Validation errors
- Missing configuration

## Running Examples

Each example is self-contained and can be run independently:

```bash
# Make sure you're in the project root
cd /path/to/blogus

# Run any example
python examples/basic_usage.py
python examples/template_management.py
python examples/cross_model.py
```

## Output

Examples provide rich output with:
- ✅ Success indicators
- ❌ Error messages
- 🧪 Process indicators
- 📊 Summary statistics
- 📝 Detailed results

## Next Steps

1. Try running the examples with your own prompts
2. Modify the examples to test different models
3. Create your own templates
4. Explore the CLI interface: `blogus --help`
5. Try the web API: `blogus-web`
6. Build a custom application using the clean architecture
