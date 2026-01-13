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

### Running Locally

Generate art from a local Python repository:

```bash
# Basic usage
pycasso /path/to/your/repo -o artwork.png

# With custom style
pycasso /path/to/your/repo --style "Cyberpunk neon graffiti" -o art.png

# Show the code analysis summary (verbose mode)
pycasso /path/to/your/repo -v -o art.png

# Using a config file (auto-discovers pycasso.toml in current directory)
pycasso /path/to/your/repo -o art.png

# Explicit config file path
pycasso /path/to/your/repo -c pycasso.toml -o art.png
```

**Example:**
```bash
# Generate art for a Flask project
pycasso ~/projects/flask-app -o flask-art.png

# Generate art with custom style
pycasso ~/projects/django-site --style "Minimalist zen black and white" -o zen-art.png
```

### Running with GitHub URL

Generate art directly from a GitHub repository (it will be cloned automatically):

```bash
# Basic usage from GitHub
pycasso https://github.com/owner/repo -o artwork.png

# With custom style
pycasso https://github.com/owner/repo --style "Retro 80s arcade" -o retro-art.png

# Show the code analysis summary
pycasso https://github.com/owner/repo -v -o art.png
```

**Examples:**
```bash
# Generate art for a popular Python project
pycasso https://github.com/psf/requests -o requests-art.png

# Generate art with verbose output
pycasso https://github.com/django/django --style "Abstract digital art" -v -o django-art.png

# Generate art for a smaller repository
pycasso https://github.com/username/my-python-lib -o my-lib-art.png
```

### Running the Web Server

Start a Flask web server with a health endpoint:

```bash
pycasso-serve
```

The server runs on `http://127.0.0.1:5000`. Check the health endpoint:

```bash
curl http://127.0.0.1:5000/health
# Returns: {"status": "ok"}
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