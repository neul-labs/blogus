# Examples

Real-world examples and use cases for Blogus.

---

## Quick Examples

### Basic Chat Assistant

```yaml
# prompts/chat-assistant.prompt
---
name: chat-assistant
description: General-purpose conversational assistant
model:
  id: gpt-4o
  temperature: 0.7
  max_tokens: 1000
variables:
  - name: user_message
    type: string
    required: true
    description: The user's message to respond to
  - name: context
    type: string
    description: Optional conversation context
tags:
  - chat
  - general
---
You are a helpful, friendly AI assistant. Your goal is to provide accurate, helpful responses while being conversational and approachable.

Guidelines:
- Be concise but thorough
- Ask clarifying questions when needed
- Admit when you don't know something
- Use appropriate formatting (lists, code blocks) when helpful

{{#context}}
Previous context:
{{context}}
{{/context}}

User: {{user_message}}
```

**Usage:**

```bash
blogus exec chat-assistant --var user_message="What's the best way to learn Python?"
```

---

### Content Summarizer

```yaml
# prompts/summarizer.prompt
---
name: summarizer
description: Summarize content into key points
model:
  id: gpt-4o
  temperature: 0.3
  max_tokens: 500
variables:
  - name: content
    type: string
    required: true
    description: Content to summarize
  - name: format
    type: string
    default: bullets
    enum: [bullets, paragraph, numbered]
    description: Output format
  - name: length
    type: string
    default: medium
    enum: [brief, medium, detailed]
    description: Summary length
  - name: audience
    type: string
    default: general
    description: Target audience
tags:
  - summarization
  - content
---
You are an expert content summarizer. Analyze the following content and create a {{length}} summary in {{format}} format, tailored for a {{audience}} audience.

Length guidelines:
- brief: 2-3 key points
- medium: 4-6 key points
- detailed: 7-10 key points

Content:
---
{{content}}
---

Provide your summary:
```

**Usage:**

```bash
blogus exec summarizer \
  --var content="$(cat article.txt)" \
  --var format=bullets \
  --var length=medium \
  --var audience="technical team"
```

---

### Code Reviewer

```yaml
# prompts/code-reviewer.prompt
---
name: code-reviewer
description: Review code for bugs, security, and best practices
model:
  id: claude-3-sonnet-20240229
  temperature: 0.2
  max_tokens: 2000
variables:
  - name: code
    type: string
    required: true
    description: Code to review
  - name: language
    type: string
    required: true
    description: Programming language
  - name: focus
    type: string
    default: all
    enum: [all, security, performance, style, bugs]
    description: Review focus area
  - name: severity_threshold
    type: string
    default: low
    enum: [low, medium, high, critical]
    description: Minimum severity to report
tags:
  - code
  - review
  - development
---
You are a senior software engineer conducting a code review. Review the following {{language}} code with a focus on {{focus}} issues.

Report issues with severity {{severity_threshold}} or higher.

For each issue found, provide:
1. **Location**: Line number or code section
2. **Severity**: Critical / High / Medium / Low
3. **Category**: Bug / Security / Performance / Style / Maintainability
4. **Description**: What the issue is
5. **Suggestion**: How to fix it

Code to review:
```{{language}}
{{code}}
```

Begin your review:
```

**Usage:**

```bash
blogus exec code-reviewer \
  --var code="$(cat src/auth.py)" \
  --var language=python \
  --var focus=security \
  --var severity_threshold=medium
```

---

### Email Composer

```yaml
# prompts/email-composer.prompt
---
name: email-composer
description: Compose professional emails
model:
  id: gpt-4o
  temperature: 0.6
  max_tokens: 800
variables:
  - name: purpose
    type: string
    required: true
    description: Purpose of the email
  - name: recipient
    type: string
    required: true
    description: Who the email is for
  - name: tone
    type: string
    default: professional
    enum: [professional, friendly, formal, casual]
    description: Email tone
  - name: key_points
    type: string
    description: Key points to include
  - name: sender_name
    type: string
    default: "[Your name]"
    description: Name of sender
tags:
  - email
  - communication
  - business
---
Compose a {{tone}} email for the following purpose:

Purpose: {{purpose}}
Recipient: {{recipient}}
Sender: {{sender_name}}

{{#key_points}}
Key points to include:
{{key_points}}
{{/key_points}}

Requirements:
- Keep it concise and clear
- Use appropriate greeting and sign-off for {{tone}} tone
- Structure with clear paragraphs
- Include a clear call-to-action if appropriate

Generate the email (subject line and body):
```

**Usage:**

```bash
blogus exec email-composer \
  --var purpose="Schedule a meeting to discuss Q1 results" \
  --var recipient="Marketing team" \
  --var tone=professional \
  --var key_points="Revenue up 15%, new product launch success, areas for improvement"
```

---

## Industry Examples

### E-commerce: Product Description Generator

```yaml
# prompts/product-description.prompt
---
name: product-description
description: Generate compelling product descriptions for e-commerce
model:
  id: gpt-4o
  temperature: 0.7
  max_tokens: 600
variables:
  - name: product_name
    type: string
    required: true
  - name: features
    type: string
    required: true
    description: Key product features (comma-separated)
  - name: target_audience
    type: string
    required: true
  - name: brand_voice
    type: string
    default: modern
    enum: [luxury, modern, playful, technical, eco-friendly]
  - name: include_seo
    type: boolean
    default: true
tags:
  - ecommerce
  - marketing
  - copywriting
---
You are an expert e-commerce copywriter. Create a compelling product description for:

Product: {{product_name}}
Key Features: {{features}}
Target Audience: {{target_audience}}
Brand Voice: {{brand_voice}}

{{#include_seo}}
Include SEO-optimized content with natural keyword integration.
{{/include_seo}}

Structure your response as:
1. **Headline** (attention-grabbing, 8 words max)
2. **Hook** (1-2 sentences that create desire)
3. **Features & Benefits** (bullet points linking features to customer benefits)
4. **Social Proof Placeholder** (where reviews would go)
5. **Call to Action** (compelling CTA)

Generate the product description:
```

---

### Healthcare: Patient Communication

```yaml
# prompts/patient-communication.prompt
---
name: patient-communication
description: Generate patient-friendly medical communications
model:
  id: gpt-4o
  temperature: 0.4
  max_tokens: 800
variables:
  - name: topic
    type: string
    required: true
    description: Medical topic to explain
  - name: reading_level
    type: string
    default: 8th-grade
    enum: [6th-grade, 8th-grade, high-school, college]
  - name: communication_type
    type: string
    default: explanation
    enum: [explanation, instructions, reminder, follow-up]
  - name: include_next_steps
    type: boolean
    default: true
tags:
  - healthcare
  - patient-education
  - compliance
---
You are a healthcare communication specialist. Create a {{communication_type}} about the following topic, written at a {{reading_level}} reading level.

Topic: {{topic}}

Guidelines:
- Use simple, everyday language
- Avoid medical jargon (or explain it when necessary)
- Be empathetic and reassuring
- Use short sentences and paragraphs
- Include practical, actionable information

{{#include_next_steps}}
Include clear next steps the patient should take.
{{/include_next_steps}}

IMPORTANT: This is for informational purposes only. Include a note to consult their healthcare provider for personalized advice.

Generate the patient communication:
```

---

### Legal: Contract Clause Explainer

```yaml
# prompts/contract-explainer.prompt
---
name: contract-explainer
description: Explain legal contract clauses in plain language
model:
  id: claude-3-sonnet-20240229
  temperature: 0.2
  max_tokens: 1000
variables:
  - name: clause_text
    type: string
    required: true
    description: The contract clause to explain
  - name: audience
    type: string
    default: business-owner
    enum: [business-owner, consumer, employee, general]
  - name: jurisdiction
    type: string
    default: general
    description: Jurisdiction context (e.g., "California", "EU", "general")
tags:
  - legal
  - contracts
  - explanation
---
You are a legal communication specialist (not providing legal advice). Explain the following contract clause in plain language for a {{audience}}.

Contract Clause:
---
{{clause_text}}
---

Jurisdiction context: {{jurisdiction}}

Provide:
1. **Plain Language Summary** (2-3 sentences, no jargon)
2. **What This Means For You** (practical implications)
3. **Key Points to Note** (important details, potential concerns)
4. **Questions to Consider** (things the reader might want to clarify)

DISCLAIMER: This explanation is for informational purposes only and does not constitute legal advice. Consult with a qualified attorney for specific legal guidance.

Explain the clause:
```

---

### Finance: Investment Analysis

```yaml
# prompts/investment-analysis.prompt
---
name: investment-analysis
description: Analyze investment opportunities
model:
  id: gpt-4o
  temperature: 0.3
  max_tokens: 1500
variables:
  - name: company_info
    type: string
    required: true
    description: Company information and financials
  - name: analysis_type
    type: string
    default: fundamental
    enum: [fundamental, technical, qualitative, comprehensive]
  - name: investment_horizon
    type: string
    default: medium-term
    enum: [short-term, medium-term, long-term]
  - name: risk_tolerance
    type: string
    default: moderate
    enum: [conservative, moderate, aggressive]
tags:
  - finance
  - investment
  - analysis
---
You are a financial analyst. Perform a {{analysis_type}} analysis of the following investment opportunity, considering a {{investment_horizon}} investment horizon and {{risk_tolerance}} risk tolerance.

Company/Investment Information:
---
{{company_info}}
---

Provide:
1. **Executive Summary** (2-3 sentences)
2. **Key Metrics Analysis** (relevant to {{analysis_type}} analysis)
3. **Strengths** (bullish factors)
4. **Risks** (bearish factors and concerns)
5. **Comparable Analysis** (if applicable)
6. **Conclusion** (overall assessment)

DISCLAIMER: This analysis is for educational purposes only and does not constitute investment advice. Past performance does not guarantee future results. Consult with a qualified financial advisor before making investment decisions.

Begin analysis:
```

---

## Integration Examples

### Python Integration

```python
# app/services/ai_service.py
from blogus import load_prompt, execute_prompt
from blogus.core import TargetLLMModel

class AIService:
    def __init__(self, model: str = "gpt-4o"):
        self.model = model

    def summarize(self, content: str, format: str = "bullets") -> str:
        """Summarize content using the summarizer prompt."""
        prompt = load_prompt("summarizer",
            content=content,
            format=format,
            length="medium",
            audience="general"
        )
        return execute_prompt(prompt, self.model)

    def review_code(self, code: str, language: str) -> dict:
        """Review code using the code-reviewer prompt."""
        prompt = load_prompt("code-reviewer",
            code=code,
            language=language,
            focus="all",
            severity_threshold="low"
        )
        response = execute_prompt(prompt, self.model)
        return self._parse_review(response)

    def _parse_review(self, response: str) -> dict:
        # Parse the structured review response
        # ...
        pass


# Usage
service = AIService()
summary = service.summarize(article_content)
review = service.review_code(python_code, "python")
```

---

### FastAPI Integration

```python
# app/api/routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from blogus import load_prompt, execute_prompt

router = APIRouter()

class SummarizeRequest(BaseModel):
    content: str
    format: str = "bullets"
    length: str = "medium"

class SummarizeResponse(BaseModel):
    summary: str
    model: str
    tokens_used: int

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    try:
        prompt = load_prompt("summarizer",
            content=request.content,
            format=request.format,
            length=request.length,
            audience="general"
        )

        result = execute_prompt(prompt, "gpt-4o", return_usage=True)

        return SummarizeResponse(
            summary=result.content,
            model="gpt-4o",
            tokens_used=result.usage.total_tokens
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

### LangChain Integration

```python
# app/chains/summarization.py
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.llms import OpenAI
from blogus import load_prompt

def create_summarization_chain():
    """Create a LangChain chain using Blogus prompt."""

    # Load the Blogus prompt
    blogus_prompt = load_prompt("summarizer")

    # Convert to LangChain format
    template = blogus_prompt.template
    variables = blogus_prompt.variables

    langchain_prompt = PromptTemplate(
        input_variables=[v.name for v in variables],
        template=template
    )

    llm = OpenAI(
        model=blogus_prompt.model.id,
        temperature=blogus_prompt.model.temperature
    )

    return LLMChain(llm=llm, prompt=langchain_prompt)


# Usage
chain = create_summarization_chain()
result = chain.run(content="Article text...", format="bullets", length="medium")
```

---

## CI/CD Examples

### GitHub Actions Workflow

```yaml
# .github/workflows/prompts.yml
name: Prompt Management

on:
  push:
    paths:
      - 'prompts/**'
      - 'prompts.lock'
  pull_request:
    paths:
      - 'prompts/**'

jobs:
  verify:
    name: Verify Prompts
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Blogus
        run: pip install blogus

      - name: Verify lock file
        run: blogus verify --strict

  analyze:
    name: Analyze Changed Prompts
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Blogus
        run: pip install blogus

      - name: Get changed prompts
        id: changed
        run: |
          CHANGED=$(git diff --name-only origin/${{ github.base_ref }}...HEAD -- 'prompts/*.prompt')
          echo "files=$CHANGED" >> $GITHUB_OUTPUT

      - name: Analyze prompts
        if: steps.changed.outputs.files != ''
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          for file in ${{ steps.changed.outputs.files }}; do
            echo "Analyzing $file..."
            blogus analyze "$file" --json >> analysis.json
          done

      - name: Comment on PR
        if: steps.changed.outputs.files != ''
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const analysis = fs.readFileSync('analysis.json', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '## Prompt Analysis\n```json\n' + analysis + '\n```'
            })
```

---

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: blogus-check
        name: Check for unversioned prompts
        entry: blogus check --fail-on-unversioned
        language: system
        pass_filenames: false

      - id: blogus-verify
        name: Verify prompt lock file
        entry: blogus verify
        language: system
        pass_filenames: false
        files: ^prompts/
```

---

## Testing Examples

### Prompt Test Suite

```python
# tests/test_prompts.py
import pytest
from blogus import load_prompt, execute_prompt
from blogus.testing import PromptTestCase, PromptTestRunner

class TestSummarizerPrompt:
    """Test suite for the summarizer prompt."""

    @pytest.fixture
    def prompt(self):
        return load_prompt("summarizer")

    def test_bullet_format(self, prompt):
        """Test bullet point output format."""
        result = execute_prompt(prompt,
            content="Test content with multiple points.",
            format="bullets",
            length="brief"
        )
        assert "•" in result or "-" in result or "*" in result

    def test_respects_length(self, prompt):
        """Test that length parameter is respected."""
        brief = execute_prompt(prompt,
            content="Long article...",
            format="bullets",
            length="brief"
        )
        detailed = execute_prompt(prompt,
            content="Long article...",
            format="bullets",
            length="detailed"
        )
        # Detailed should be longer
        assert len(detailed) > len(brief)

    def test_handles_empty_content(self, prompt):
        """Test graceful handling of empty content."""
        result = execute_prompt(prompt,
            content="",
            format="bullets",
            length="brief"
        )
        # Should not crash, should indicate no content
        assert result is not None


# Run with generated test cases
def test_with_generated_cases():
    """Run tests using Blogus-generated test cases."""
    runner = PromptTestRunner("summarizer")
    results = runner.run_generated_tests()

    assert results.passed >= results.total * 0.8  # 80% pass rate
```

---

### Integration Test

```python
# tests/integration/test_prompt_workflow.py
import subprocess
import tempfile
import os

def test_full_workflow():
    """Test the complete Blogus workflow."""

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test Python file with LLM call
        test_file = os.path.join(tmpdir, "test.py")
        with open(test_file, "w") as f:
            f.write('''
import openai
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "system", "content": "You are helpful."}]
)
''')

        # Scan
        result = subprocess.run(
            ["blogus", "scan", tmpdir],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "Found 1 LLM API call" in result.stdout

        # Init
        result = subprocess.run(
            ["blogus", "init", "--dir", os.path.join(tmpdir, "prompts"), "--no-interactive"],
            capture_output=True, text=True,
            cwd=tmpdir
        )
        assert result.returncode == 0

        # Lock
        result = subprocess.run(
            ["blogus", "lock"],
            capture_output=True, text=True,
            cwd=tmpdir
        )
        assert result.returncode == 0
        assert os.path.exists(os.path.join(tmpdir, "prompts.lock"))

        # Verify
        result = subprocess.run(
            ["blogus", "verify"],
            capture_output=True, text=True,
            cwd=tmpdir
        )
        assert result.returncode == 0
```
