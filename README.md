# Pycasso

Transform Python repositories into AI-generated art.

Pycasso scans your Python codebase, analyses the AST structure, and uses AI to generate unique artwork inspired by your code.

## Installation

```bash
poetry install
```

## Usage

Generate art using OpenRouter's LLM capabilities. Set up your API key first:

```bash
# Copy the example env file
cp .env.example .env

# Add your OpenRouter API key
# Get a free key at https://openrouter.ai/keys
echo "OPENROUTER_API_KEY=your_key_here" >> .env
```

Then generate artwork:

```bash
# Basic usage
pycasso /path/to/repo -o artwork.png

# With custom style
pycasso /path/to/repo --style "Cyberpunk neon graffiti" -o art.png

# Using a config file
pycasso /path/to/repo -c pycasso.toml -o art.png

# Show the generated prompt
pycasso /path/to/repo -v -o art.png
```

## Configuration

Create a `pycasso.toml` in your repo root to customise the output:

```toml
[canvas]
width = 3840
height = 2160

[colors]
background = "#121212"    # Deep Midnight
class = "#FF007F"         # Cyber Magenta
function = "#00FFFF"      # Electric Cyan
loop = "#F5D300"          # Neon Yellow
conditional = "#FF6B35"   # Orange

[exclude]
dirs = ["venv", "__pycache__", ".git", ".venv", "node_modules"]

[ai]
style = "Synthwave / Dark Mode IDE aesthetic, neon colors, abstract geometric"
prompt_model = "openai/gpt-4.1"
image_model = "google/gemini-2.0-flash-exp:free"
```

### AI Configuration Details

- `style`: Describes the desired art style. This is passed to GPT-4.1 when crafting the image prompt.
- `prompt_model`: The LLM used to generate image prompts from code. Recommend `openai/gpt-4.1` for quality.
- `image_model`: The model used to generate the final image. Recommend `google/gemini-2.0-flash-exp:free` (free tier).

Both models are accessed via OpenRouter. Pricing varies; check [OpenRouter pricing](https://openrouter.ai) for details.

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

- `src/pycasso/cli_ai.py` — CLI entry point
- `src/pycasso/harvest.py` — File discovery
- `src/pycasso/parse.py` — AST parsing
- `src/pycasso/condense.py` — Code summary generator for AI
- `src/pycasso/llm.py` — OpenRouter API client
- `src/pycasso/config.py` — Configuration management

### Adding Features

When adding new features, update tests in `tests/` directory:

```bash
# Run specific test file
poetry run pytest tests/test_llm.py -v

# Run with coverage
poetry run pytest --cov=src/pycasso
```

## License

MIT