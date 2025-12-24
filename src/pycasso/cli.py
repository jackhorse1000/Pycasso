import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from .condense import condense
from .config import load_config
from .github import (
    GitHubError,
    PrivateRepoError,
    check_repo_public,
    cleanup_repo,
    clone_repo,
    is_github_url,
    parse_github_url,
)
from .harvest import harvest
from .llm import LLMConfig, LLMError, generate_image, generate_prompt, get_api_key
from .parse import parse


def _get_unique_output_path(base_path: Path) -> Path:
    if not base_path.exists():
        return base_path

    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent

    counter = 1
    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        prog="pycasso",
        description="Generate AI artwork from Python repositories",
    )
    parser.add_argument(
        "source",
        type=str,
        help="Path to Python repository or GitHub URL (e.g., https://github.com/owner/repo)",
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("output/art.png"), help="Output image path"
    )
    parser.add_argument("--style", type=str, help="Art style (overrides config)")
    parser.add_argument("-c", "--config", type=Path, help="Path to config file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show code summary")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )
    logger = logging.getLogger(__name__)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    is_github = is_github_url(args.source)
    cloned_path: Path | None = None

    try:
        if is_github:
            try:
                github_repo = parse_github_url(args.source)
                logger.info("")
                logger.info("═" * 60)
                logger.info("  PYCASSO: Generating artwork from code")
                logger.info("═" * 60)
                logger.info("")
                logger.info("🔒 Checking repository accessibility...")
                logger.info("   Repository: %s/%s", github_repo.owner, github_repo.name)
                check_repo_public(github_repo)
                logger.info("   ✓ Repository is public")
                logger.info("")
                logger.info("🌐 Cloning repository...")
                cloned_path = clone_repo(github_repo)
                repo_path = cloned_path
                logger.info("   ✓ Cloned to temporary directory")
            except PrivateRepoError as e:
                logger.error("")
                logger.error("❌ %s", e)
                logger.error("")
                logger.error("   Tip: Make sure the repository URL is correct and the repo is public.")
                sys.exit(1)
            except GitHubError as e:
                logger.error("GitHub error: %s", e)
                sys.exit(1)
        else:
            repo_path = Path(args.source).resolve()
            if not repo_path.exists():
                logger.error("Path does not exist: %s", repo_path)
                sys.exit(1)
            logger.info("")
            logger.info("═" * 60)
            logger.info("  PYCASSO: Generating artwork from code")
            logger.info("═" * 60)
            logger.info("")

        try:
            api_key = get_api_key()
        except LLMError as e:
            logger.error(str(e))
            sys.exit(1)

        # Auto-discover config: CLI flag > cwd > defaults
        config_path = args.config
        if config_path is None:
            cwd_config = Path.cwd() / "pycasso.toml"
            if cwd_config.exists():
                config_path = cwd_config
                logger.info("📄 Using config: %s", config_path)

        config = load_config(config_path)
        style = args.style or config.ai.style

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

            # Ensure output directory exists and get unique filename
            args.output.parent.mkdir(parents=True, exist_ok=True)
            output_path = _get_unique_output_path(args.output)
            output_path.write_bytes(image_data)
            logger.info("")
            logger.info("═" * 60)
            logger.info("✅ Success! Saved image to: %s", output_path)
            logger.info("═" * 60)

        except LLMError as e:
            logger.error("LLM error: %s", e)
            sys.exit(1)

    finally:
        # Clean up cloned repository
        if cloned_path is not None:
            logger.info("")
            logger.info("🧹 Cleaning up temporary files...")
            cleanup_repo(cloned_path)


if __name__ == "__main__":
    main()
