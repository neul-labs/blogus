# Advanced Features

Blogus provides advanced features for sophisticated prompt engineering workflows.

## Prompt Evolution

Implement evolutionary algorithms for prompt optimization:

```python
from blogus.core import analyze_prompt, JudgeLLMModel, get_llm_response

class PromptEvolver:
    def __init__(self, judge_model: str):
        self.judge_model = judge_model

    def mutate_prompt(self, prompt: str) -> str:
        """Apply improvements to a prompt."""
        mutation_prompt = f"""
Take the following prompt and make a small, beneficial modification:

Original prompt: {prompt}

Modified prompt:
"""
        return get_llm_response(mutation_prompt, self.judge_model)

    def evolve_prompt(self, initial_prompt: str, generations: int = 10) -> str:
        """Evolve a prompt over multiple generations."""
        current_prompt = initial_prompt

        for generation in range(generations):
            analysis = analyze_prompt(current_prompt, self.judge_model)

            if analysis.overall_goal_alignment >= 9:
                break

            mutated_prompt = self.mutate_prompt(current_prompt)
            mutated_analysis = analyze_prompt(mutated_prompt, self.judge_model)

            if mutated_analysis.overall_goal_alignment > analysis.overall_goal_alignment:
                current_prompt = mutated_prompt
                print(f"Generation {generation + 1}: Improved to {mutated_analysis.overall_goal_alignment}/10")

        return current_prompt

# Usage
evolver = PromptEvolver(JudgeLLMModel.GPT_4)
optimized_prompt = evolver.evolve_prompt("You are a helpful assistant.")
```

---

## Cross-Model Comparison

Systematically compare prompt performance across models:

```python
from blogus.core import execute_prompt, TargetLLMModel
from typing import Dict, List

class ModelComparison:
    def __init__(self, target_models: List[TargetLLMModel]):
        self.target_models = target_models

    def compare_execution(self, prompt: str) -> Dict[str, str]:
        """Execute prompt on all target models."""
        results = {}
        for model in self.target_models:
            try:
                response = execute_prompt(prompt, model)
                results[model.value] = response
            except Exception as e:
                results[model.value] = f"Error: {str(e)}"
        return results

# Usage
models = [
    TargetLLMModel.GPT_4,
    TargetLLMModel.CLAUDE_3_SONNET,
    TargetLLMModel.GROQ_LLAMA3_70B
]

comparator = ModelComparison(models)
results = comparator.compare_execution("Explain photosynthesis.")

for model, response in results.items():
    print(f"\n{model}:\n{response[:200]}...")
```

---

## Test Dataset Management

Create and manage comprehensive test datasets:

```python
from blogus.core import generate_test, JudgeLLMModel
from typing import List, Dict
import json

class TestDataset:
    def __init__(self, prompt_template: str):
        self.prompt_template = prompt_template
        self.test_cases = []

    def generate_test_cases(self, judge_model: str, num_cases: int = 10):
        """Generate multiple test cases."""
        for i in range(num_cases):
            try:
                test_case = generate_test(self.prompt_template, judge_model)
                self.test_cases.append({
                    'id': i,
                    'input': test_case.input,
                    'expected_output': test_case.expected_output,
                    'goal_relevance': test_case.goal_relevance
                })
            except Exception as e:
                print(f"Failed to generate test case {i}: {e}")

    def save_to_file(self, filename: str):
        """Save test dataset to JSON file."""
        dataset = {
            'prompt_template': self.prompt_template,
            'test_cases': self.test_cases
        }
        with open(filename, 'w') as f:
            json.dump(dataset, f, indent=2)

    def load_from_file(self, filename: str):
        """Load test dataset from JSON file."""
        with open(filename, 'r') as f:
            dataset = json.load(f)
        self.prompt_template = dataset['prompt_template']
        self.test_cases = dataset['test_cases']

# Usage
dataset = TestDataset("Translate {text} from {source_lang} to {target_lang}")
dataset.generate_test_cases(JudgeLLMModel.GPT_4, 20)
dataset.save_to_file("translation_tests.json")
```

---

## Prompt Version Tracking

Track prompt evolution with version control:

```python
from datetime import datetime
from typing import List, Dict
import hashlib

class PromptVersion:
    def __init__(self, prompt: str, goal: str = None, metadata: Dict = None):
        self.prompt = prompt
        self.goal = goal
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        self.version_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute a hash of the prompt content."""
        content = f"{self.prompt}|{self.goal}|{sorted(self.metadata.items())}"
        return hashlib.md5(content.encode()).hexdigest()

class PromptTracker:
    def __init__(self, initial_prompt: str, initial_goal: str = None):
        self.versions: List[PromptVersion] = []
        initial_version = PromptVersion(initial_prompt, initial_goal)
        self.versions.append(initial_version)
        self.current_version = 0

    def update_prompt(self, new_prompt: str, new_goal: str = None, metadata: Dict = None):
        """Add a new version of the prompt."""
        new_version = PromptVersion(new_prompt, new_goal, metadata)

        if new_version.version_hash != self.versions[-1].version_hash:
            self.versions.append(new_version)
            self.current_version = len(self.versions) - 1
            return True
        return False

    def get_changelog(self) -> List[Dict]:
        """Get a changelog of all versions."""
        changelog = []
        for i, version in enumerate(self.versions):
            changelog.append({
                'version': i,
                'timestamp': version.timestamp.isoformat(),
                'hash': version.version_hash,
                'is_current': i == self.current_version
            })
        return changelog

# Usage
tracker = PromptTracker(
    "You are a helpful assistant.",
    "Provide helpful responses to user queries"
)

tracker.update_prompt(
    "You are a helpful assistant. Always be concise and accurate.",
    "Provide helpful, concise, and accurate responses",
    {'improvement_reason': 'Added conciseness requirement'}
)

print(f"Total versions: {len(tracker.versions)}")
```

---

## CI/CD Integration

Integrate Blogus into automated testing pipelines:

```python
from blogus.core import analyze_prompt, execute_prompt, JudgeLLMModel, TargetLLMModel
import sys

def run_prompt_tests(prompt_file: str, threshold: int = 7) -> bool:
    """Run automated tests on a prompt."""
    with open(prompt_file, 'r') as f:
        prompt = f.read()

    # Analyze prompt quality
    analysis = analyze_prompt(prompt, JudgeLLMModel.GPT_4)

    print(f"Prompt alignment score: {analysis.overall_goal_alignment}/10")
    print(f"Estimated effectiveness: {analysis.estimated_effectiveness}/10")

    # Check if prompt meets quality threshold
    if analysis.overall_goal_alignment < threshold:
        print(f"FAIL: Prompt quality below threshold of {threshold}")
        return False

    print("PASS: Prompt meets quality threshold")
    return True

# Usage in CI/CD
if __name__ == "__main__":
    prompt_file = sys.argv[1] if len(sys.argv) > 1 else "prompt.txt"
    success = run_prompt_tests(prompt_file)
    sys.exit(0 if success else 1)
```

### GitHub Actions Example

```yaml
name: Prompt Quality Check

on:
  push:
    paths:
      - 'prompts/**'
  pull_request:
    paths:
      - 'prompts/**'

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Blogus
        run: pip install blogus

      - name: Verify prompts
        run: blogus verify
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

      - name: Analyze prompts
        run: |
          for prompt in prompts/*.prompt; do
            echo "Analyzing $prompt..."
            blogus analyze "$prompt" --json
          done
```

---

## Custom Analysis Prompts

Create custom analysis workflows:

```python
from blogus.core import get_llm_response, JudgeLLMModel

def analyze_for_bias(prompt: str, judge_model: str) -> str:
    """Analyze a prompt for potential bias."""
    analysis_prompt = f"""
Analyze the following prompt for potential bias and fairness issues:

Prompt: {prompt}

Consider:
1. Gender bias
2. Cultural assumptions
3. Age-related bias
4. Socioeconomic assumptions
5. Accessibility considerations

Provide specific findings and recommendations.
"""
    return get_llm_response(analysis_prompt, judge_model)

def analyze_for_safety(prompt: str, judge_model: str) -> str:
    """Analyze a prompt for safety concerns."""
    analysis_prompt = f"""
Analyze the following prompt for potential safety issues:

Prompt: {prompt}

Consider:
1. Potential for harmful outputs
2. Privacy concerns
3. Jailbreak vulnerabilities
4. Prompt injection risks
5. Data leakage potential

Provide specific findings and recommendations.
"""
    return get_llm_response(analysis_prompt, judge_model)

# Usage
prompt = "You are a helpful assistant for financial advice."
bias_analysis = analyze_for_bias(prompt, JudgeLLMModel.CLAUDE_3_OPUS)
safety_analysis = analyze_for_safety(prompt, JudgeLLMModel.CLAUDE_3_OPUS)
```

---

## Prompt Templates with Inheritance

Build composable prompt templates:

```python
class PromptTemplate:
    def __init__(self, name: str, content: str, parent: 'PromptTemplate' = None):
        self.name = name
        self.content = content
        self.parent = parent

    def render(self, **variables) -> str:
        """Render the template with variables."""
        result = self.content

        # Include parent content if exists
        if self.parent:
            parent_content = self.parent.render(**variables)
            result = f"{parent_content}\n\n{result}"

        # Substitute variables
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))

        return result

# Usage
base_assistant = PromptTemplate(
    "base-assistant",
    "You are a helpful AI assistant. Be clear and concise."
)

python_tutor = PromptTemplate(
    "python-tutor",
    "Your specialty is teaching Python programming. Use examples when explaining concepts.",
    parent=base_assistant
)

prompt = python_tutor.render(topic="list comprehensions")
```

---

## Web API Endpoints

Blogus provides a REST API when running the web server:

### Start the Server

```bash
blogus-web --port 8000
```

### Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/infer-goal` | Infer prompt goal |
| POST | `/api/analyze-fragments` | Analyze prompt fragments |
| POST | `/api/analyze-logs` | Generate prompt logs |
| POST | `/api/analyze-prompt` | Full prompt analysis |
| POST | `/api/generate-test` | Generate test case |
| POST | `/api/execute-prompt` | Execute a prompt |

### Example Request

```bash
curl -X POST http://localhost:8000/api/analyze-prompt \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "You are a helpful assistant.",
    "judge_model": "gpt-4o"
  }'
```

### Response

```json
{
  "overall_goal_alignment": 7,
  "suggested_improvements": [
    "Add specific domain expertise",
    "Include response format guidelines"
  ],
  "estimated_effectiveness": 6,
  "inferred_goal": "Provide helpful responses to user queries",
  "is_goal_inferred": true
}
```

---

## Prompt Development Lifecycle

### 1. Initial Creation

Start with a basic prompt:

```python
from blogus.core import analyze_prompt, JudgeLLMModel

prompt = "You are a helpful assistant."
analysis = analyze_prompt(prompt, JudgeLLMModel.GPT_4)
```

### 2. Iterative Enhancement

Improve based on analysis:

```python
from blogus.core import analyze_fragments, JudgeLLMModel

fragments = analyze_fragments(prompt, JudgeLLMModel.GPT_4)

for fragment in fragments:
    print(f"Fragment: {fragment.text}")
    print(f"Alignment: {fragment.goal_alignment}/5")
    print(f"Suggestion: {fragment.improvement_suggestion}")
```

### 3. Cross-Model Validation

Test across different models:

```bash
blogus exec my-prompt --model gpt-4o
blogus exec my-prompt --model claude-3-haiku-20240307
blogus exec my-prompt --model groq/llama3-70b-8192
```

### 4. Test Dataset Generation

Generate test cases:

```bash
blogus test "Translate {text} to French" --count 10 --output tests.json
```

### 5. Version Control

Lock and verify:

```bash
blogus lock
git add prompts/ prompts.lock
git commit -m "Update prompts"
```

### 6. CI Integration

Verify in CI:

```bash
blogus verify || exit 1
```
