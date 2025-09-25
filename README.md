# Blogus: Craft, Analyze, and Perfect Your AI Prompts

![Blogus Logo](https://via.placeholder.com/150?text=Blogus)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/blogus.svg)](https://badge.fury.io/py/blogus)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

## Why Blogus?

In the rapidly evolving field of AI and large language models, crafting effective prompts has become a crucial skill. Blogus is born out of the need for a sophisticated, user-friendly tool that empowers developers, researchers, and AI enthusiasts to:

- Analyze and refine prompts in real-time
- Generate and manage test cases
- Execute prompts across multiple AI models
- Visualize and understand prompt effectiveness
- Separate target models (for execution) from judge models (for analysis)
- Manage the complete prompt development lifecycle

Whether you're a seasoned prompt engineer or just starting your journey with AI, Blogus provides the tools you need to elevate your prompt crafting skills.

## What is Blogus?

Blogus is an advanced prompt engineering tool available as:
1. **A Python library** for programmatic use in your applications
2. **A command-line interface** for quick analysis and testing
3. **A web interface** with an intuitive frontend for interactive prompt engineering

Key features include:

- **Real-time Prompt Analysis**: Get instant feedback on your prompts' effectiveness and alignment with your goals.
- **Multi-model Support**: Test your prompts across various AI models, including GPT-4, Claude, and more.
- **Test Case Generation**: Automatically generate relevant test cases for your prompts.
- **Interactive Code Editor**: A feature-rich editor with syntax highlighting and real-time analysis feedback (in web UI).
- **Execution Environment**: Run your prompts and see the results immediately.
- **Test Case Management**: Store and download generated test cases as JSON files (in web UI).
- **Dynamic Goal Inference**: Automatically infer the goal of your prompt if not provided.
- **Target vs Judge Models**: Separate models for prompt execution and analysis for optimal cost and performance.
- **Complete Prompt Lifecycle**: Tools for the entire prompt engineering workflow from creation to optimization.

## Documentation

Comprehensive documentation is available in the [docs](docs/) directory:

- [Getting Started](docs/getting_started.md) - Installation and basic setup
- [Core Concepts](docs/core_concepts.md) - Understanding the fundamentals of Blogus
- [Prompt Development Lifecycle](docs/prompt_lifecycle.md) - Complete workflow for prompt engineering
- [Command Line Interface](docs/cli.md) - Using Blogus from the command line
- [Web Interface](docs/web_interface.md) - Using the web-based interface
- [Library Usage](docs/library.md) - Integrating Blogus into your Python applications
- [Model Selection](docs/models.md) - Choosing the right models for your tasks
- [Advanced Features](docs/advanced.md) - Advanced techniques and workflows
- [API Reference](docs/api/) - Detailed API documentation
- [Contributing](docs/contributing.md) - How to contribute to Blogus

## Examples

Check out the [examples](examples/) directory for practical usage examples:

- [Basic Analysis](examples/basic_analysis.py) - Simple prompt analysis and execution
- [Test Generation](examples/test_generation.py) - Generating test cases for parameterized prompts
- [Cross-Model Comparison](examples/cross_model.py) - Comparing prompt responses across different models

## Installation

```bash
pip install blogus
```

For web interface support, install with the web extra:
```bash
pip install blogus[web]
```

## Usage

### As a Library

```python
from blogus.core import TargetLLMModel, JudgeLLMModel, analyze_prompt, generate_test

prompt = "You are an AI assistant that helps people find information..."

# Analyze a prompt using a judge model
analysis = analyze_prompt(prompt, JudgeLLMModel.GPT_4)
print(f"Goal alignment: {analysis.overall_goal_alignment}/10")

# Generate a test case using a judge model
test_case = generate_test(prompt, JudgeLLMModel.GPT_4)

# Execute a prompt using a target model
result = execute_prompt(prompt, TargetLLMModel.GPT_4)
```

### Command Line Interface

```bash
# Analyze a prompt with separate target and judge models
blogus analyze "You are an AI assistant that helps people find information..." \\
  --target-model gpt-4o \\
  --judge-model claude-3-opus-20240229

# Generate a test case with separate target and judge models
blogus test "You are an AI assistant that helps people find information..." \\
  --target-model gpt-4o \\
  --judge-model claude-3-opus-20240229

# Execute a prompt with a target model
blogus execute "You are an AI assistant that helps people find information..." \\
  --target-model gpt-4o

# Infer the goal of a prompt with a judge model
blogus goal "You are an AI assistant that helps people find information..." \\
  --judge-model claude-3-opus-20240229

# See all available commands
blogus --help
```

### Web Interface

To run the web interface:
```bash
blogus-web  # If installed with web extras
# or
python -m blogus.web
```

Then navigate to `http://localhost:8000` in your browser.

## API Keys

Blogus uses LiteLLM to support a wide range of AI models. You'll need API keys for the models you want to use:

- OpenAI API key for GPT models
- Anthropic API key for Claude models
- Groq API key for Mixtral/Llama models

Set these as environment variables:
```bash
export OPENAI_API_KEY=your_openai_api_key
export ANTHROPIC_API_KEY=your_anthropic_api_key
export GROQ_API_KEY=your_groq_api_key
```

For other models supported by LiteLLM, please refer to the [LiteLLM documentation](https://docs.litellm.ai/docs/) for the required environment variables.

## Contributing

We welcome contributions to Blogus! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to get started.

## License

Blogus is open-source software licensed under the MIT license. See the [LICENSE](LICENSE) file for more details.

## Support

If you encounter any issues or have questions, please file an issue on our [GitHub issue tracker](https://github.com/terraprompt/blogus/issues).

## Citation

If you use Blogus in your research, please cite it as follows:

```bibtex
@article{sarkar2024blogus,
  title={Blogus: An Advanced Tool for Crafting, Analyzing, and Perfecting AI Prompts},
  author={Sarkar, Dipankar},
  journal={arXiv preprint arXiv:2024.xxxxx},
  year={2024},
  url={https://github.com/terraprompt/blogus},
  note={Software available from https://github.com/terraprompt/blogus},
  abstract={Blogus is an open-source software tool designed to facilitate the
    process of prompt engineering for large language models. It provides
    real-time analysis of prompts, supports multiple AI models, and offers
    features for test case generation and prompt execution. This tool aims to
    enhance the efficiency and effectiveness of prompt crafting in AI research
    and applications.}
}
```

For LaTeX users, you can use the following command to cite Blogus:

```latex
\cite{sarkar2024blogus}
```

---

Happy Prompt Engineering with Blogus! 🚀
