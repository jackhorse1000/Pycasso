import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from .condense import condense
from .config import load_config
from .harvest import harvest
from .llm import LLMConfig, LLMError, generate_image, generate_prompt, get_api_key
from .parse import parse


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        prog="pycasso-ai",
        description="Generate AI artwork from Python repositories",
    )
    parser.add_argument("path", type=Path, help="Path to Python repository")
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("art.png"), help="Output image path"
    )
    parser.add_argument("--style", type=str, help="Art style (overrides config)")
    parser.add_argument("-c", "--config", type=Path, help="Path to config file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show generated prompt")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )
    logger = logging.getLogger(__name__)

    repo_path = args.path.resolve()
    if not repo_path.exists():
        logger.error("Path does not exist: %s", repo_path)
        sys.exit(1)

    try:
        api_key = get_api_key()
    except LLMError as e:
        logger.error(str(e))
        sys.exit(1)

    config = load_config(args.config)
    style = args.style or config.ai.style

    logger.info("Harvesting Python files from %s...", repo_path)
    files = list(harvest(repo_path, config.exclude.dirs))

    if not files:
        logger.error("No Python files found")
        sys.exit(1)

    logger.info("Found %d Python files", len(files))

    logger.info("Parsing entities...")
    entities = []
    for file_path in files:
        entities.extend(parse(file_path))

    logger.info("Extracted %d entities", len(entities))

    logger.info("Condensing code summary...")
    summary = condense(entities, repo_path)

    if args.verbose:
        logger.debug("Code summary:\n%s", summary)

    llm_config = LLMConfig(
        api_key=api_key,
        prompt_model=config.ai.prompt_model,
        image_model=config.ai.image_model,
    )

    try:
        logger.info("Generating image prompt with %s...", config.ai.prompt_model)
        image_prompt = generate_prompt(summary, style, llm_config)

        if args.verbose:
            logger.debug("Generated prompt:\n%s", image_prompt)

        logger.info("Generating image with %s...", config.ai.image_model)
        image_data = generate_image(image_prompt, llm_config)

        args.output.write_bytes(image_data)
        logger.info("Saved image to %s", args.output)

    except LLMError as e:
        logger.error("LLM error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
