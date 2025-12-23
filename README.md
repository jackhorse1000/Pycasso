# Pycasso

Transform Python repositories into Synthwave-styled generative art.

Pycasso scans your Python codebase, analyses the AST structure, and renders a deterministic abstract artwork where each code construct becomes a geometric shape.

## Installation

```bash
poetry install
```

## Usage

```bash
# Generate art from a Python repo
pycasso /path/to/repo -o artwork.png

# Use a specific seed for reproducibility
pycasso /path/to/repo --seed 42 -o artwork.png

# Use a custom config file
pycasso /path/to/repo -c pycasso.toml -o artwork.png

# Verbose output
pycasso /path/to/repo -v -o artwork.png
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
```

## Visual Language

| Code Entity | Shape | Colour |
|-------------|-------|--------|
| Class | Hollow Square | Magenta |
| Function | Solid Circle | Cyan |
| Loop | Arc | Yellow |
| Conditional | Triangle | Orange |

## Determinism

The same code + same seed = identical image. Change the seed to "remix" the layout, or change the code to see localised visual diffs.

## Development

```bash
# Run tests
poetry run pytest

# Run with verbose logging
poetry run pycasso . -v
```

## License

MIT