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
        level=logging.INFO,
        format="%(message)s",
    )
    logger = logging.getLogger(__name__)

    # Suppress noisy httpx debug logs even in verbose mode
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

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

    logger.info("")
    logger.info("═" * 60)
    logger.info("  PYCASSO-AI: Generating artwork from code")
    logger.info("═" * 60)
    logger.info("")

    # Step 1: Harvest files
    logger.info("📂 Step 1: Harvesting Python files")
    logger.info("   Source: %s", repo_path)
    files = list(harvest(repo_path, config.exclude.dirs))

    if not files:
        logger.error("No Python files found")
        sys.exit(1)

    logger.info("   Found %d Python files", len(files))

    # Step 2: Parse entities
    logger.info("")
    logger.info("🔍 Step 2: Parsing code entities")
    entities = []
    for file_path in files:
        entities.extend(parse(file_path))

    class_count = sum(1 for e in entities if e.entity_type.name == "CLASS")
    func_count = sum(1 for e in entities if e.entity_type.name == "FUNCTION")
    logger.info("   Extracted %d entities (%d classes, %d functions)", len(entities), class_count, func_count)

    # Step 3: Condense summary
    logger.info("")
    logger.info("📝 Step 3: Condensing code summary")
    summary = condense(entities, repo_path)

    if args.verbose:
        logger.info("")
        logger.info("─" * 40)
        logger.info("Code Summary:")
        logger.info("─" * 40)
        for line in summary.split("\n"):
            logger.info("   %s", line)
        logger.info("─" * 40)

    llm_config = LLMConfig(
        api_key=api_key,
        prompt_model=config.ai.prompt_model,
        image_model=config.ai.image_model,
    )

    try:
        # Step 4: Generate prompt
        logger.info("")
        logger.info("🤖 Step 4: Generating image prompt")
        logger.info("   Model: %s", config.ai.prompt_model)
        logger.info("   Style: %s", style)
        image_prompt = generate_prompt(summary, style, llm_config)

        logger.info("")
        logger.info("─" * 40)
        logger.info("Generated Image Prompt:")
        logger.info("─" * 40)
        for line in image_prompt.split("\n"):
            logger.info("   %s", line)
        logger.info("─" * 40)

        # Step 5: Generate image
        logger.info("")
        logger.info("🎨 Step 5: Generating image")
        logger.info("   Model: %s", config.ai.image_model)
        image_data = generate_image(image_prompt, llm_config)

        args.output.write_bytes(image_data)
        logger.info("")
        logger.info("═" * 60)
        logger.info("✅ Success! Saved image to: %s", args.output)
        logger.info("═" * 60)

    except LLMError as e:
        logger.error("LLM error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
