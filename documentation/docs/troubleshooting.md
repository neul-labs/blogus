# Troubleshooting

Common issues and solutions when using Blogus.

---

## Installation Issues

### "Command not found: blogus"

**Symptoms:**
```bash
$ blogus
bash: blogus: command not found
```

**Solutions:**

1. **Check if installed:**
   ```bash
   pip show blogus
   ```

2. **Add to PATH (if using pip with --user):**
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   export PATH="$HOME/.local/bin:$PATH"
   source ~/.bashrc
   ```

3. **Use python -m:**
   ```bash
   python -m blogus --help
   ```

4. **Reinstall:**
   ```bash
   pip uninstall blogus
   pip install blogus
   ```

---

### "ModuleNotFoundError: No module named 'blogus'"

**Symptoms:**
```python
>>> from blogus import load_prompt
ModuleNotFoundError: No module named 'blogus'
```

**Solutions:**

1. **Check virtual environment:**
   ```bash
   # Make sure you're in the right venv
   which python
   pip list | grep blogus
   ```

2. **Install in current environment:**
   ```bash
   pip install blogus
   ```

3. **Check Python version:**
   ```bash
   python --version  # Must be 3.9+
   ```

---

### "Web extras not installed"

**Symptoms:**
```bash
$ blogus-web
Error: Web dependencies not installed. Run: pip install blogus[web]
```

**Solutions:**
```bash
pip install blogus[web]
# or
uv add blogus[web]
```

---

## API Key Issues

### "OPENAI_API_KEY not set"

**Symptoms:**
```
Error: API key not found. Set OPENAI_API_KEY environment variable.
```

**Solutions:**

1. **Set environment variable:**
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

2. **Use .env file:**
   ```bash
   # .env
   OPENAI_API_KEY=sk-...
   ```

3. **Check if set correctly:**
   ```bash
   echo $OPENAI_API_KEY
   # Should show your key (or at least sk-...)
   ```

4. **For different providers:**
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   export GROQ_API_KEY="gsk_..."
   ```

---

### "Invalid API key" or "Authentication failed"

**Symptoms:**
```
Error: Authentication failed. Check your API key.
litellm.AuthenticationError: Invalid API Key
```

**Solutions:**

1. **Verify key is correct:**
   - Check for extra spaces or newlines
   - Ensure you copied the complete key
   - Try regenerating the key in your provider's dashboard

2. **Check key permissions:**
   - Some API keys have restricted permissions
   - Ensure your key has access to the models you're using

3. **Test key directly:**
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

---

### "Rate limit exceeded"

**Symptoms:**
```
Error: Rate limit exceeded. Please retry after X seconds.
litellm.RateLimitError: Rate limit reached
```

**Solutions:**

1. **Wait and retry:**
   ```bash
   # Blogus will auto-retry with exponential backoff
   blogus analyze prompt.prompt --timeout 120
   ```

2. **Use a different model:**
   ```bash
   # Try a less popular model
   blogus analyze prompt.prompt --judge-model gpt-3.5-turbo
   ```

3. **Batch requests:**
   ```bash
   # Process fewer prompts at once
   blogus analyze prompts/chat.prompt
   # Wait, then
   blogus analyze prompts/summarize.prompt
   ```

4. **Upgrade API tier:**
   - Check your provider's rate limits
   - Consider upgrading for higher limits

---

## Scan Issues

### "No LLM calls found"

**Symptoms:**
```bash
$ blogus scan
Found 0 LLM API calls.
```

**Solutions:**

1. **Check file patterns:**
   ```bash
   # Scan specific file types
   blogus scan --include "**/*.py" --include "**/*.js"
   ```

2. **Check exclusions:**
   ```bash
   # Don't exclude your source files
   blogus scan --exclude "nothing"
   ```

3. **Verify code patterns:**
   Blogus looks for standard SDK patterns:
   ```python
   # These ARE detected:
   openai.chat.completions.create(...)
   anthropic.messages.create(...)
   litellm.completion(...)

   # These might NOT be detected:
   my_custom_wrapper(prompt)  # Custom wrappers
   client.invoke(...)          # Non-standard methods
   ```

4. **Try verbose mode:**
   ```bash
   blogus scan -vv
   ```

---

### "Scan is slow"

**Solutions:**

1. **Exclude unnecessary directories:**
   ```bash
   blogus scan \
     --exclude "**/node_modules/**" \
     --exclude "**/venv/**" \
     --exclude "**/.git/**" \
     --exclude "**/dist/**"
   ```

2. **Scan specific directories:**
   ```bash
   blogus scan ./src ./lib
   ```

3. **Use non-recursive for quick check:**
   ```bash
   blogus scan --no-recursive ./src
   ```

---

## Prompt File Issues

### "Invalid YAML in prompt file"

**Symptoms:**
```
Error: Failed to parse prompts/my-prompt.prompt
yaml.scanner.ScannerError: mapping values are not allowed here
```

**Solutions:**

1. **Check YAML syntax:**
   ```yaml
   # Wrong - missing quotes around special characters
   description: This prompt: does stuff

   # Correct
   description: "This prompt: does stuff"
   ```

2. **Check indentation:**
   ```yaml
   # Wrong - inconsistent indentation
   model:
     id: gpt-4o
      temperature: 0.7  # Wrong indent!

   # Correct
   model:
     id: gpt-4o
     temperature: 0.7
   ```

3. **Validate YAML:**
   ```bash
   python -c "import yaml; yaml.safe_load(open('prompts/my-prompt.prompt'))"
   ```

4. **Check frontmatter delimiters:**
   ```yaml
   ---
   name: my-prompt
   ---
   # Make sure there are exactly three dashes
   ```

---

### "Variable not found"

**Symptoms:**
```
Error: Variable 'user_name' not found in prompt template
```

**Solutions:**

1. **Check variable names match:**
   ```yaml
   variables:
     - name: userName  # camelCase
   ---
   Hello {{userName}}  # Must match exactly
   ```

2. **Provide all required variables:**
   ```bash
   blogus exec my-prompt \
     --var userName="John" \
     --var message="Hello"
   ```

3. **Check for typos:**
   ```yaml
   # Template uses {{user_name}}
   # But variable defined as 'userName'
   ```

---

### "Hash mismatch" during verify

**Symptoms:**
```
✗ assistant-summarize: Hash mismatch (file was modified)
```

**Solutions:**

1. **Update the lock file:**
   ```bash
   blogus lock
   git add prompts.lock
   git commit -m "Update prompt lock file"
   ```

2. **If you didn't intend to change the prompt:**
   ```bash
   # Restore from git
   git checkout -- prompts/assistant-summarize.prompt
   ```

3. **Check for whitespace changes:**
   ```bash
   git diff --ignore-space-change prompts/
   ```

---

## Execution Issues

### "Model not found"

**Symptoms:**
```
Error: Model 'gpt-5' not found
litellm.NotFoundError: The model `gpt-5` does not exist
```

**Solutions:**

1. **Check model name:**
   ```bash
   # Common model names:
   gpt-4o
   gpt-4-turbo
   gpt-3.5-turbo
   claude-3-opus-20240229
   claude-3-sonnet-20240229
   claude-3-haiku-20240307
   ```

2. **Check provider prefix:**
   ```bash
   # For Groq models, use prefix:
   groq/llama3-70b-8192
   groq/mixtral-8x7b-32768
   ```

3. **Check API access:**
   - Some models require special access
   - Verify your API plan includes the model

---

### "Context length exceeded"

**Symptoms:**
```
Error: This model's maximum context length is 8192 tokens
```

**Solutions:**

1. **Use a model with longer context:**
   ```bash
   blogus exec my-prompt \
     --model claude-3-sonnet-20240229  # 200K context
   ```

2. **Reduce input size:**
   ```bash
   # Truncate long inputs
   blogus exec summarize --var text="$(head -c 10000 long_file.txt)"
   ```

3. **Set max_tokens in prompt:**
   ```yaml
   model:
     id: gpt-4o
     max_tokens: 1000  # Limit response size
   ```

---

### "Timeout" errors

**Symptoms:**
```
Error: Request timed out after 60 seconds
```

**Solutions:**

1. **Increase timeout:**
   ```bash
   blogus exec my-prompt --timeout 120
   ```

2. **Use streaming:**
   ```bash
   blogus exec my-prompt --stream
   ```

3. **Check network:**
   ```bash
   curl -I https://api.openai.com
   ```

4. **Use a faster model:**
   ```bash
   blogus exec my-prompt --model gpt-3.5-turbo
   ```

---

## Lock File Issues

### "Lock file not found"

**Symptoms:**
```
Error: prompts.lock not found
```

**Solutions:**

1. **Generate lock file:**
   ```bash
   blogus lock
   ```

2. **Check path:**
   ```bash
   blogus verify --lock ./path/to/prompts.lock
   ```

---

### "Prompt not in lock file"

**Symptoms:**
```
Warning: new-prompt: Not in lock file
```

**Solutions:**

1. **Add to lock file:**
   ```bash
   blogus lock
   ```

2. **If prompt should be ignored:**
   ```bash
   blogus lock --exclude "new-prompt.prompt"
   ```

---

## CI/CD Issues

### "Verify fails in CI but works locally"

**Common Causes:**

1. **Lock file not committed:**
   ```bash
   git add prompts.lock
   git commit -m "Update lock file"
   git push
   ```

2. **Different line endings:**
   ```bash
   # In .gitattributes
   *.prompt text eol=lf
   prompts.lock text eol=lf
   ```

3. **File permissions:**
   ```bash
   chmod 644 prompts/*.prompt
   chmod 644 prompts.lock
   ```

4. **Missing prompts directory:**
   ```yaml
   # In CI, ensure prompts are checked out
   - uses: actions/checkout@v4
     with:
       fetch-depth: 0
   ```

---

### "API key not available in CI"

**Solutions:**

1. **GitHub Actions:**
   ```yaml
   - name: Verify prompts
     run: blogus verify
     env:
       OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
   ```

2. **GitLab CI:**
   ```yaml
   variables:
     OPENAI_API_KEY: $OPENAI_API_KEY
   ```

3. **For verify (no API needed):**
   ```bash
   # blogus verify doesn't need API keys
   # It only checks file hashes
   blogus verify  # Works without API key
   ```

---

## Performance Issues

### "Analysis is slow"

**Solutions:**

1. **Use faster models for testing:**
   ```bash
   blogus analyze prompt.prompt --judge-model gpt-3.5-turbo
   ```

2. **Skip detailed analysis:**
   ```bash
   # Don't use --detailed for quick checks
   blogus analyze prompt.prompt
   ```

3. **Batch operations:**
   ```bash
   # Analyze multiple prompts in sequence
   for f in prompts/*.prompt; do
     blogus analyze "$f" --json >> results.json
   done
   ```

---

### "Memory usage is high"

**Solutions:**

1. **Process fewer files:**
   ```bash
   blogus scan ./src/specific_module
   ```

2. **Use streaming for large outputs:**
   ```bash
   blogus exec large-prompt --stream
   ```

---

## Getting More Help

### Enable Debug Logging

```bash
blogus -vv scan
# or
BLOGUS_DEBUG=1 blogus scan
```

### Check Version

```bash
blogus --version
pip show blogus
```

### Report a Bug

1. Search [existing issues](https://github.com/your-username/blogus/issues)
2. Create a [new issue](https://github.com/your-username/blogus/issues/new) with:
   - Blogus version (`blogus --version`)
   - Python version (`python --version`)
   - OS and version
   - Complete error message
   - Steps to reproduce
   - Expected vs actual behavior

### Community Support

- [GitHub Discussions](https://github.com/your-username/blogus/discussions)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/blogus) (tag: `blogus`)
