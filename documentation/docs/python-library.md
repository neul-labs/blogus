# Python Library

Comprehensive guide to using Blogus as a Python library for programmatic prompt management and analysis.

---

## Installation

```bash
pip install blogus
```

For web interface features:

```bash
pip install blogus[web]
```

For development:

```bash
pip install blogus[dev]
```

---

## Quick Start

```python
from blogus import load_prompt, execute_prompt
from blogus.core import analyze_prompt, JudgeLLMModel

# Load and execute a prompt
prompt = load_prompt("summarizer", content="Your text here")
response = execute_prompt(prompt, "gpt-4o")
print(response)

# Analyze a prompt
analysis = analyze_prompt(
    "You are a helpful assistant.",
    JudgeLLMModel.GPT_4
)
print(f"Goal alignment: {analysis.overall_goal_alignment}/10")
```

---

## Core Module

### Importing

```python
from blogus.core import (
    # Functions
    analyze_prompt,
    execute_prompt,
    analyze_fragments,
    generate_test,
    infer_goal,
    analyze_logs,
    get_llm_response,

    # Data classes
    PromptAnalysis,
    Fragment,
    Test,
    Log,

    # Enums
    TargetLLMModel,
    JudgeLLMModel,
)
```

---

## Functions

### analyze_prompt

Perform a comprehensive analysis of a prompt's effectiveness.

```python
def analyze_prompt(
    prompt: str,
    judge_model: str,
    goal: Optional[str] = None
) -> PromptAnalysis
```

**Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `prompt` | `str` | The prompt text to analyze | Required |
| `judge_model` | `str` | Model to use for analysis | Required |
| `goal` | `str` | Expected goal (auto-inferred if not provided) | `None` |

**Returns:** `PromptAnalysis` object

**Example:**

```python
from blogus.core import analyze_prompt, JudgeLLMModel

# Basic analysis
prompt = """
You are a helpful assistant. Your goal is to provide
accurate, concise answers to user questions.
"""

analysis = analyze_prompt(prompt, JudgeLLMModel.GPT_4)

print(f"Goal Alignment: {analysis.overall_goal_alignment}/10")
print(f"Effectiveness: {analysis.estimated_effectiveness}/10")
print(f"Goal: {analysis.inferred_goal}")
print(f"Was goal inferred: {analysis.is_goal_inferred}")

print("\nSuggestions:")
for i, suggestion in enumerate(analysis.suggested_improvements, 1):
    print(f"  {i}. {suggestion}")
```

**With explicit goal:**

```python
analysis = analyze_prompt(
    prompt="You are a Python tutor.",
    judge_model=JudgeLLMModel.CLAUDE_3_OPUS,
    goal="Teach Python programming to beginners effectively"
)
```

---

### execute_prompt

Execute a prompt using a target LLM and get the response.

```python
def execute_prompt(
    prompt: str,
    target_model: str,
    **kwargs
) -> str
```

**Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `prompt` | `str` | The prompt to execute | Required |
| `target_model` | `str` | Model to use for execution | Required |
| `**kwargs` | Various | Additional parameters passed to the model | - |

**Returns:** `str` - The model's response

**Example:**

```python
from blogus.core import execute_prompt, TargetLLMModel

# Simple execution
response = execute_prompt(
    "Explain quantum computing in simple terms.",
    TargetLLMModel.GPT_4
)
print(response)

# With additional parameters
response = execute_prompt(
    "Write a haiku about programming.",
    TargetLLMModel.GPT_4,
    temperature=0.9,
    max_tokens=100
)
print(response)
```

---

### analyze_fragments

Analyze individual fragments of a prompt for goal alignment.

```python
def analyze_fragments(
    prompt: str,
    judge_model: str,
    goal: Optional[str] = None
) -> List[Fragment]
```

**Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `prompt` | `str` | The prompt to analyze | Required |
| `judge_model` | `str` | Model to use for analysis | Required |
| `goal` | `str` | Expected goal | `None` (auto-inferred) |

**Returns:** `List[Fragment]` - List of analyzed fragments

**Example:**

```python
from blogus.core import analyze_fragments, JudgeLLMModel

prompt = """
You are a helpful assistant.
Always be polite and respectful.
Here's an example of how to respond:
Q: What is the weather like?
A: I don't have access to real-time weather data.
Never provide medical or legal advice.
"""

fragments = analyze_fragments(prompt, JudgeLLMModel.CLAUDE_3_OPUS)

for i, fragment in enumerate(fragments, 1):
    print(f"\nFragment {i}:")
    print(f"  Text: {fragment.text[:50]}...")
    print(f"  Type: {fragment.type}")
    print(f"  Alignment: {fragment.goal_alignment}/5")
    print(f"  Suggestion: {fragment.improvement_suggestion}")
```

---

### generate_test

Generate test cases for a prompt template.

```python
def generate_test(
    prompt: str,
    judge_model: str,
    goal: Optional[str] = None
) -> Test
```

**Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `prompt` | `str` | The prompt template | Required |
| `judge_model` | `str` | Model to use for generation | Required |
| `goal` | `str` | Expected goal | `None` (auto-inferred) |

**Returns:** `Test` - Generated test case

**Example:**

```python
from blogus.core import generate_test, JudgeLLMModel

prompt_template = """
Translate the following {source_language} text to {target_language}:

{text}

Provide only the translation, no explanations.
"""

test_case = generate_test(prompt_template, JudgeLLMModel.GPT_4)

print(f"Input variables: {test_case.input}")
print(f"Expected output: {test_case.expected_output}")
print(f"Goal relevance: {test_case.goal_relevance}/5")
```

**Generate multiple test cases:**

```python
def generate_test_suite(prompt_template: str, num_tests: int = 5) -> list:
    """Generate multiple test cases for a prompt."""
    tests = []
    for _ in range(num_tests):
        test = generate_test(prompt_template, JudgeLLMModel.GPT_4)
        tests.append(test)
    return tests

test_suite = generate_test_suite(prompt_template, 10)
for i, test in enumerate(test_suite, 1):
    print(f"Test {i}: {test.input}")
```

---

### infer_goal

Infer the intended goal of a prompt.

```python
def infer_goal(
    prompt: str,
    model: str
) -> str
```

**Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `prompt` | `str` | The prompt to analyze | Required |
| `model` | `str` | Model to use for inference | Required |

**Returns:** `str` - The inferred goal

**Example:**

```python
from blogus.core import infer_goal, JudgeLLMModel

prompt = """
You are a financial advisor who helps people plan for retirement.
You should consider their risk tolerance, time horizon, and goals.
Always recommend diversified portfolios.
"""

goal = infer_goal(prompt, JudgeLLMModel.CLAUDE_3_OPUS)
print(f"Inferred goal: {goal}")
# Output: "Help users create personalized retirement plans..."
```

---

### analyze_logs

Generate diagnostic logs for a prompt.

```python
def analyze_logs(
    prompt: str,
    judge_model: str,
    goal: Optional[str] = None
) -> List[Log]
```

**Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `prompt` | `str` | The prompt to analyze | Required |
| `judge_model` | `str` | Model to use for analysis | Required |
| `goal` | `str` | Expected goal | `None` (auto-inferred) |

**Returns:** `List[Log]` - List of diagnostic logs

**Example:**

```python
from blogus.core import analyze_logs, JudgeLLMModel

prompt = "You are a helpful assistant. Always be nice."

logs = analyze_logs(prompt, JudgeLLMModel.GPT_4)

for log in logs:
    emoji = {"info": "ℹ️", "warning": "⚠️", "error": "❌"}.get(log.type, "•")
    print(f"{emoji} [{log.type.upper()}] {log.message}")
```

---

### get_llm_response

Low-level function to get a raw response from an LLM.

```python
def get_llm_response(
    model: str,
    prompt: str,
    max_tokens: int = 1000
) -> str
```

**Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `model` | `str` | The LLM model to use | Required |
| `prompt` | `str` | The prompt to send | Required |
| `max_tokens` | `int` | Maximum tokens to generate | `1000` |

**Returns:** `str` - The raw response

**Example:**

```python
from blogus.core import get_llm_response

# Custom analysis workflow
analysis_prompt = f"""
Analyze this prompt for potential bias:

{user_prompt}

List any biases found.
"""

response = get_llm_response("gpt-4o", analysis_prompt, max_tokens=500)
print(response)
```

---

## Data Classes

### PromptAnalysis

Represents a comprehensive analysis of a prompt.

```python
@dataclass
class PromptAnalysis:
    overall_goal_alignment: int      # 1-10 scale
    suggested_improvements: List[str]
    estimated_effectiveness: int     # 1-10 scale
    inferred_goal: Optional[str]
    is_goal_inferred: bool
```

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `overall_goal_alignment` | `int` | How well the prompt aligns with its goal (1-10) |
| `suggested_improvements` | `List[str]` | Specific improvement suggestions |
| `estimated_effectiveness` | `int` | How effective the prompt is (1-10) |
| `inferred_goal` | `str` | The inferred goal if not provided |
| `is_goal_inferred` | `bool` | Whether the goal was inferred |

**Example:**

```python
analysis = PromptAnalysis(
    overall_goal_alignment=8,
    suggested_improvements=[
        "Add specific examples",
        "Clarify output format"
    ],
    estimated_effectiveness=7,
    inferred_goal="Help users with general questions",
    is_goal_inferred=True
)

# Access attributes
if analysis.overall_goal_alignment >= 7:
    print("Prompt meets quality threshold")

# Iterate suggestions
for suggestion in analysis.suggested_improvements:
    print(f"- {suggestion}")
```

---

### Fragment

Represents a fragment of a prompt with analysis.

```python
@dataclass
class Fragment:
    text: str
    type: str  # instruction, context, example, constraint
    goal_alignment: int  # 1-5 scale
    improvement_suggestion: str
```

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `text` | `str` | The fragment text |
| `type` | `str` | Fragment type (instruction/context/example/constraint) |
| `goal_alignment` | `int` | Alignment with goal (1-5) |
| `improvement_suggestion` | `str` | How to improve this fragment |

**Fragment Types:**

- `instruction`: Direct instructions to the model
- `context`: Background information or context
- `example`: Few-shot examples
- `constraint`: Restrictions or limitations

---

### Test

Represents a test case for a prompt.

```python
@dataclass
class Test:
    input: Dict[str, str]
    expected_output: str
    goal_relevance: int  # 1-5 scale
```

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `input` | `Dict[str, str]` | Input variable values |
| `expected_output` | `str` | Expected model output |
| `goal_relevance` | `int` | How relevant the test is (1-5) |

**Example:**

```python
test = Test(
    input={
        "source_language": "English",
        "target_language": "French",
        "text": "Hello, world!"
    },
    expected_output="Bonjour, monde!",
    goal_relevance=5
)

# Use in testing
prompt_with_vars = template.format(**test.input)
response = execute_prompt(prompt_with_vars, model)

# Compare (simplified)
if test.expected_output.lower() in response.lower():
    print("Test passed!")
```

---

### Log

Represents a diagnostic log entry.

```python
@dataclass
class Log:
    type: str  # info, warning, error
    message: str
```

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `type` | `str` | Log level (info/warning/error) |
| `message` | `str` | The log message |

---

## Model Enums

### TargetLLMModel

Enumeration of models for prompt execution.

```python
class TargetLLMModel(str, Enum):
    # OpenAI
    GPT_4 = "gpt-4o"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"

    # Anthropic
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"

    # Groq
    GROQ_LLAMA3_70B = "groq/llama3-70b-8192"
    GROQ_MIXTRAL_8X7B = "groq/mixtral-8x7b-32768"
    GROQ_GEMMA_7B = "groq/gemma-7b-it"
```

**Usage:**

```python
from blogus.core import TargetLLMModel, execute_prompt

# Use enum value
response = execute_prompt(prompt, TargetLLMModel.GPT_4)

# Use string directly
response = execute_prompt(prompt, "gpt-4o")

# List available models
for model in TargetLLMModel:
    print(f"{model.name}: {model.value}")
```

### JudgeLLMModel

Enumeration of models for prompt analysis (same values as TargetLLMModel).

```python
from blogus.core import JudgeLLMModel

# Use for analysis
analysis = analyze_prompt(prompt, JudgeLLMModel.CLAUDE_3_OPUS)
```

---

## Prompt Loading

### load_prompt

Load a prompt from a `.prompt` file and substitute variables.

```python
from blogus import load_prompt

# Load with variables
prompt = load_prompt(
    "summarizer",
    content="Article text here...",
    format="bullets",
    length="medium"
)

# Execute
response = execute_prompt(prompt, "gpt-4o")
```

### Prompt Object

```python
from blogus import Prompt

# Load from file
prompt = Prompt.from_file("prompts/summarizer.prompt")

# Access metadata
print(f"Name: {prompt.name}")
print(f"Description: {prompt.description}")
print(f"Model: {prompt.model.id}")
print(f"Variables: {[v.name for v in prompt.variables]}")

# Render with variables
rendered = prompt.render(
    content="Text to summarize",
    format="bullets"
)

# Convert to OpenAI format
openai_params = prompt.to_openai()
response = openai.chat.completions.create(**openai_params)

# Convert to Anthropic format
anthropic_params = prompt.to_anthropic()
response = anthropic.messages.create(**anthropic_params)
```

---

## Advanced Usage

### Async Support

```python
import asyncio
from blogus.core import analyze_prompt_async, execute_prompt_async

async def analyze_multiple(prompts: list) -> list:
    """Analyze multiple prompts concurrently."""
    tasks = [
        analyze_prompt_async(p, "gpt-4o")
        for p in prompts
    ]
    return await asyncio.gather(*tasks)

async def main():
    prompts = [
        "You are a helpful assistant.",
        "You are a Python expert.",
        "You are a financial advisor."
    ]

    results = await analyze_multiple(prompts)

    for prompt, result in zip(prompts, results):
        print(f"{prompt[:30]}... → {result.overall_goal_alignment}/10")

asyncio.run(main())
```

### Streaming Responses

```python
from blogus.core import execute_prompt_stream

async def stream_response():
    async for chunk in execute_prompt_stream(
        "Tell me a long story about a dragon.",
        "gpt-4o"
    ):
        print(chunk, end="", flush=True)

asyncio.run(stream_response())
```

### Custom Analysis Pipeline

```python
from blogus.core import (
    analyze_prompt,
    analyze_fragments,
    analyze_logs,
    infer_goal,
    JudgeLLMModel
)

def comprehensive_analysis(prompt: str) -> dict:
    """Run a complete analysis pipeline."""
    model = JudgeLLMModel.CLAUDE_3_OPUS

    # Infer goal first
    goal = infer_goal(prompt, model)

    # Run all analyses
    analysis = analyze_prompt(prompt, model, goal)
    fragments = analyze_fragments(prompt, model, goal)
    logs = analyze_logs(prompt, model, goal)

    return {
        "goal": goal,
        "analysis": analysis,
        "fragments": fragments,
        "logs": logs,
        "summary": {
            "alignment": analysis.overall_goal_alignment,
            "effectiveness": analysis.estimated_effectiveness,
            "fragment_count": len(fragments),
            "warnings": len([l for l in logs if l.type == "warning"]),
            "errors": len([l for l in logs if l.type == "error"])
        }
    }

result = comprehensive_analysis("You are a helpful assistant.")
print(f"Overall score: {result['summary']['alignment']}/10")
```

### Error Handling

```python
from blogus.core import analyze_prompt, JudgeLLMModel
from blogus.exceptions import (
    BlogusError,
    APIError,
    RateLimitError,
    ParseError,
    ValidationError
)

def safe_analyze(prompt: str) -> dict:
    """Analyze with proper error handling."""
    try:
        analysis = analyze_prompt(prompt, JudgeLLMModel.GPT_4)
        return {"success": True, "analysis": analysis}

    except RateLimitError as e:
        return {"success": False, "error": "rate_limit", "retry_after": e.retry_after}

    except APIError as e:
        return {"success": False, "error": "api_error", "message": str(e)}

    except ParseError as e:
        return {"success": False, "error": "parse_error", "message": str(e)}

    except ValidationError as e:
        return {"success": False, "error": "validation", "message": str(e)}

    except BlogusError as e:
        return {"success": False, "error": "blogus_error", "message": str(e)}

    except Exception as e:
        return {"success": False, "error": "unexpected", "message": str(e)}
```

### Caching

```python
from functools import lru_cache
from blogus.core import analyze_prompt, JudgeLLMModel

@lru_cache(maxsize=100)
def cached_analyze(prompt: str, model: str) -> tuple:
    """Cache analysis results."""
    analysis = analyze_prompt(prompt, model)
    return (
        analysis.overall_goal_alignment,
        tuple(analysis.suggested_improvements),
        analysis.estimated_effectiveness
    )

# First call - hits API
result1 = cached_analyze("You are helpful.", JudgeLLMModel.GPT_4)

# Second call - uses cache
result2 = cached_analyze("You are helpful.", JudgeLLMModel.GPT_4)
```

---

## Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from blogus import load_prompt, execute_prompt
from blogus.core import analyze_prompt, JudgeLLMModel

app = FastAPI()

class PromptRequest(BaseModel):
    prompt_name: str
    variables: dict

class AnalyzeRequest(BaseModel):
    prompt_text: str
    goal: str | None = None

@app.post("/execute")
async def execute(request: PromptRequest):
    try:
        prompt = load_prompt(request.prompt_name, **request.variables)
        response = execute_prompt(prompt, "gpt-4o")
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    try:
        analysis = analyze_prompt(
            request.prompt_text,
            JudgeLLMModel.GPT_4,
            request.goal
        )
        return {
            "alignment": analysis.overall_goal_alignment,
            "effectiveness": analysis.estimated_effectiveness,
            "suggestions": analysis.suggested_improvements
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Django Integration

```python
# myapp/services.py
from blogus import load_prompt, execute_prompt
from blogus.core import analyze_prompt, JudgeLLMModel

class AIService:
    def __init__(self, model: str = "gpt-4o"):
        self.model = model

    def summarize(self, text: str) -> str:
        prompt = load_prompt("summarizer", content=text)
        return execute_prompt(prompt, self.model)

    def analyze_content(self, content: str) -> dict:
        analysis = analyze_prompt(content, JudgeLLMModel.GPT_4)
        return {
            "score": analysis.overall_goal_alignment,
            "suggestions": analysis.suggested_improvements
        }

# myapp/views.py
from django.http import JsonResponse
from .services import AIService

def summarize_view(request):
    text = request.POST.get("text", "")
    service = AIService()
    summary = service.summarize(text)
    return JsonResponse({"summary": summary})
```

---

## Best Practices

1. **Use Appropriate Models**
   - Use capable models (GPT-4, Claude Opus) for analysis
   - Use cost-effective models (GPT-3.5, Haiku) for simple execution

2. **Handle Errors Gracefully**
   - Always wrap API calls in try-except
   - Implement retry logic for rate limits

3. **Cache Results**
   - Cache analysis results for repeated prompts
   - Use Redis or similar for production caching

4. **Validate Outputs**
   - Check that returned objects have expected structure
   - Validate scores are within expected ranges

5. **Use Type Hints**
   - Leverage provided type hints for IDE support
   - Enable mypy for static type checking

6. **Batch Operations**
   - Use async for concurrent operations
   - Batch multiple analyses for efficiency
