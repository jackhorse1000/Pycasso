# Pycasso

Transform Python repositories into AI-generated art.

Pycasso scans your Python codebase, analyses the AST structure, and uses AI to generate unique artwork inspired by your code.

## Installation

```bash
poetry install
```

## Usage

Set up your OpenRouter API key first:

```bash
# Copy the example env file
cp .env.example .env

# Add your OpenRouter API key
# Get a free key at https://openrouter.ai/keys
echo "OPENROUTER_API_KEY=your_key_here" >> .env
```

Then generate artwork:

```bash
# Basic usage - local repository
pycasso /path/to/repo -o artwork.png

# From a GitHub URL
pycasso https://github.com/owner/repo -o artwork.png

# With custom style
pycasso /path/to/repo --style "Cyberpunk neon graffiti" -o art.png

# Using a config file (auto-discovers pycasso.toml in current directory)
pycasso /path/to/repo -o art.png

# Explicit config file
pycasso /path/to/repo -c pycasso.toml -o art.png

# Show the code summary (verbose mode)
pycasso /path/to/repo -v -o art.png
```

## Configuration

Create a `pycasso.toml` in your working directory to customise the output. It will be auto-discovered:

```toml
[exclude]
dirs = ["venv", "__pycache__", ".git", ".venv", "node_modules"]

[ai]
style = "Synthwave / Dark Mode IDE aesthetic, neon colors, abstract"
prompt_model = "anthropic/claude-haiku-4.5"
image_model = "google/gemini-2.5-flash-preview-05-20"
```

### Configuration Options

- `exclude.dirs`: Directories to skip when scanning for Python files
- `ai.style`: Art style description passed to the LLM when generating the image prompt
- `ai.prompt_model`: LLM used to generate image prompts from code analysis
- `ai.image_model`: Model used to generate the final image

Both models are accessed via [OpenRouter](https://openrouter.ai). Check their pricing for details.

### Customising the Prompt Template

The prompt template used to generate image descriptions can be edited at:

```
src/pycasso/prompts/image_prompt.txt
```

This file uses `{code_summary}` and `{style}` placeholders that are filled in at runtime.

## Development

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run with verbose logging
poetry run pycasso . -v --style "Your custom style"
```

### Project Structure

- `src/pycasso/cli.py` — CLI entry point
- `src/pycasso/harvest.py` — File discovery
- `src/pycasso/parse.py` — AST parsing and entity extraction
- `src/pycasso/condense.py` — Code summary generator
- `src/pycasso/llm.py` — OpenRouter API client
- `src/pycasso/github.py` — GitHub repository cloning
- `src/pycasso/config.py` — Configuration management
- `src/pycasso/prompts/` — Prompt templates

## License

MIT