import argparse
import logging
import sys
from pathlib import Path

from pycasso.config import load_config
from pycasso.harvest import harvest
from pycasso.parse import parse
from pycasso.render import render


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="pycasso",
        description="Transform Python repositories into Synthwave-styled generative art",
    )
    parser.add_argument("path", type=Path, help="Path to the Python repository")
    parser.add_argument("--seed", type=int, default=0, help="Random seed for deterministic output")
    parser.add_argument("-o", "--output", type=Path, default=Path("pycasso.png"), help="Output image path")
    parser.add_argument("-c", "--config", type=Path, default=None, help="Path to pycasso.toml config file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    if not args.path.is_dir():
        logger.error("Path '%s' is not a directory", args.path)
        return 1

    config_path = args.config
    if config_path is None:
        default_config = args.path / "pycasso.toml"
        if default_config.exists():
            config_path = default_config

    config = load_config(config_path)
    logger.info("Scanning %s...", args.path)

    file_paths = list(harvest(args.path, config.exclude.dirs))
    logger.info("Found %d Python files", len(file_paths))

    entities = []
    for file_path in file_paths:
        entities.extend(parse(file_path))

    logger.info("Extracted %d entities", len(entities))
    logger.info("Rendering to %s...", args.output)

    render(entities, config, args.seed, args.output)

    logger.info("Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
