# Model Selection

Choosing the right models is crucial for effective prompt engineering with Blogus.

## Target vs Judge Models

Blogus distinguishes between two types of models:

### Target Models

Target models **execute** prompts - they generate the actual responses in production.

**Use for:**

- Testing prompt performance
- Generating actual responses
- Cost-sensitive production environments
- Comparing model outputs

### Judge Models

Judge models **analyze and evaluate** prompts. These are typically more capable models that provide insightful feedback.

**Use for:**

- Prompt analysis and evaluation
- Fragment analysis
- Test case generation
- Goal inference

---

## Available Models

### OpenAI Models

| Model | Recommended For | Description |
|-------|-----------------|-------------|
| `gpt-4o` | Both | Latest multimodal model, excellent for analysis |
| `gpt-4-turbo` | Both | High-performance, good balance of capability and cost |
| `gpt-3.5-turbo` | Target | Cost-effective for simple tasks |

### Anthropic Models

| Model | Recommended For | Description |
|-------|-----------------|-------------|
| `claude-3-opus-20240229` | Judge | Most capable, ideal for detailed analysis |
| `claude-3-sonnet-20240229` | Both | Good balance of speed and capability |
| `claude-3-haiku-20240307` | Target | Fast and cost-effective |

### Groq Models

| Model | Recommended For | Description |
|-------|-----------------|-------------|
| `groq/llama3-70b-8192` | Both | High-quality responses with speed |
| `groq/mixtral-8x7b-32768` | Target | Cost-effective with good performance |
| `groq/gemma-7b-it` | Target | Lightweight tasks |

---

## Selection Strategy

### For Analysis (Judge Models)

1. **Prioritize capability over cost** - Analysis quality matters
2. **Claude 3 Opus** - Best for detailed, nuanced analysis
3. **GPT-4o** - Excellent alternative with broad capabilities
4. **Llama 3 70B** - Good open-source option

```python
from blogus.core import analyze_prompt, JudgeLLMModel

# Use a capable judge for analysis
analysis = analyze_prompt(prompt, JudgeLLMModel.CLAUDE_3_OPUS)
```

### For Execution (Target Models)

1. **Balance cost and performance** - Consider your budget
2. **Match task complexity**:
    - Simple tasks: GPT-3.5 Turbo, Mixtral, Haiku
    - Complex tasks: GPT-4o, Claude 3 Sonnet, Llama 3 70B
3. **Consider speed requirements** - Haiku and Groq for fast responses

```python
from blogus.core import execute_prompt, TargetLLMModel

# Use cost-effective model for execution
response = execute_prompt(prompt, TargetLLMModel.GROQ_MIXTRAL_8X7B)
```

---

## Recommended Combinations

### Cost-Effective Analysis

```python
# Powerful judge, economical execution
analysis = analyze_prompt(prompt, JudgeLLMModel.CLAUDE_3_OPUS)
response = execute_prompt(prompt, TargetLLMModel.GROQ_MIXTRAL_8X7B)
```

### High-Performance

```python
# Best quality for both
analysis = analyze_prompt(prompt, JudgeLLMModel.CLAUDE_3_OPUS)
response = execute_prompt(prompt, TargetLLMModel.GPT_4)
```

### Speed-Focused

```python
# Fast analysis and execution
analysis = analyze_prompt(prompt, JudgeLLMModel.CLAUDE_3_SONNET)
response = execute_prompt(prompt, TargetLLMModel.GROQ_LLAMA3_70B)
```

### Balanced

```python
# Good all-around performance
analysis = analyze_prompt(prompt, JudgeLLMModel.GPT_4)
response = execute_prompt(prompt, TargetLLMModel.CLAUDE_3_SONNET)
```

---

## Performance Comparison

### Latency (Fastest to Slowest)

1. **Groq Models** - Dedicated hardware, very fast
2. **Claude 3 Haiku** - Optimized for speed
3. **GPT-3.5 Turbo** - Generally fast
4. **Claude 3 Sonnet** - Moderate
5. **GPT-4o** - Variable based on load
6. **Claude 3 Opus** - Slower but thorough

### Cost (Lowest to Highest)

1. **Groq Gemma 7B** - Least expensive
2. **Groq Mixtral 8x7B** - Low cost
3. **GPT-3.5 Turbo** - Moderate
4. **Claude 3 Haiku** - Moderate
5. **Claude 3 Sonnet** - Higher
6. **GPT-4o / GPT-4 Turbo** - High
7. **Claude 3 Opus** - Highest

### Context Length

| Model | Context Window |
|-------|----------------|
| Claude 3 (all) | 200K tokens |
| GPT-4o | 128K tokens |
| GPT-4 Turbo | 128K tokens |
| Mixtral 8x7B | 32K tokens |
| GPT-3.5 Turbo | 16K tokens |
| Llama 3 70B | 8K tokens |
| Gemma 7B | 8K tokens |

---

## Best Practices

### 1. Match Model to Task

```python
# Detailed analysis: use capable judge
analysis = analyze_prompt(prompt, JudgeLLMModel.CLAUDE_3_OPUS)

# Simple execution: use cost-effective target
response = execute_prompt(prompt, TargetLLMModel.GROQ_MIXTRAL_8X7B)
```

### 2. Test Across Models

```python
models_to_test = [
    TargetLLMModel.GPT_3_5_TURBO,
    TargetLLMModel.GROQ_MIXTRAL_8X7B,
    TargetLLMModel.CLAUDE_3_HAIKU
]

for model in models_to_test:
    response = execute_prompt(prompt, model)
    print(f"{model.value}: {response[:100]}...")
```

### 3. Use Powerful Models for Analysis

```python
# Even with a simple target model, use powerful judge
response = execute_prompt(prompt, TargetLLMModel.GROQ_GEMMA_7B)
analysis = analyze_prompt(prompt, JudgeLLMModel.GPT_4)  # More capable
```

### 4. Consider Context Requirements

```python
# For long prompts, choose models with sufficient context
if len(prompt) > 10000:
    target_model = TargetLLMModel.CLAUDE_3_SONNET  # 200K context
else:
    target_model = TargetLLMModel.GPT_3_5_TURBO  # 16K context
```

---

## Environment Variables

Set API keys for the models you want to use:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Groq
export GROQ_API_KEY="gsk_..."
```

---

## CLI Model Selection

### Analyze Command

```bash
blogus analyze "Your prompt" --judge-model claude-3-opus-20240229
```

### Execute Command

```bash
blogus exec my-prompt --model gpt-4o
```

### Available CLI Model Values

```
gpt-4o
gpt-4-turbo
gpt-3.5-turbo
claude-3-opus-20240229
claude-3-sonnet-20240229
claude-3-haiku-20240307
groq/llama3-70b-8192
groq/mixtral-8x7b-32768
groq/gemma-7b-it
```
