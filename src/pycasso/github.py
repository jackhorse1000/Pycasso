"""GitHub repository cloning utilities for pycasso-ai."""

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import httpx


@dataclass
class GitHubRepo:
    """Parsed GitHub repository information."""

    owner: str
    name: str
    url: str

    @property
    def clone_url(self) -> str:
        """Get the HTTPS clone URL."""
        return f"https://github.com/{self.owner}/{self.name}.git"

    @property
    def api_url(self) -> str:
        """Get the GitHub API URL for this repo."""
        return f"https://api.github.com/repos/{self.owner}/{self.name}"


class GitHubError(Exception):
    """Error related to GitHub operations."""

    pass


class PrivateRepoError(GitHubError):
    """Error when trying to access a private repository."""

    pass


def is_github_url(path_or_url: str) -> bool:
    """Check if the input is a GitHub URL."""
    patterns = [
        r"^https?://github\.com/[\w.-]+/[\w.-]+",
        r"^github\.com/[\w.-]+/[\w.-]+",
        r"^git@github\.com:[\w.-]+/[\w.-]+",
    ]
    return any(re.match(pattern, path_or_url) for pattern in patterns)


def parse_github_url(url: str) -> GitHubRepo:
    """Parse a GitHub URL into owner and repo name.

    Supports formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - github.com/owner/repo
    - git@github.com:owner/repo.git
    """
    # Remove trailing slashes and .git suffix
    url = url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]

    # Handle different URL formats
    patterns = [
        r"https?://github\.com/([\w.-]+)/([\w.-]+)",
        r"github\.com/([\w.-]+)/([\w.-]+)",
        r"git@github\.com:([\w.-]+)/([\w.-]+)",
    ]

    for pattern in patterns:
        match = re.match(pattern, url)
        if match:
            owner, name = match.groups()
            return GitHubRepo(owner=owner, name=name, url=url)

    raise GitHubError(f"Could not parse GitHub URL: {url}")


def check_repo_public(repo: GitHubRepo) -> None:
    """Check if a GitHub repository is public.

    Args:
        repo: Parsed GitHub repository information

    Raises:
        PrivateRepoError: If the repository is private or doesn't exist
        GitHubError: If there's a network error
    """
    try:
        response = httpx.get(repo.api_url, timeout=10.0)

        if response.status_code == 404:
            raise PrivateRepoError(
                f"Repository '{repo.owner}/{repo.name}' not found or is private. "
                "Pycasso-ai can only access public repositories."
            )
        elif response.status_code == 403:
            # Rate limited but we can still try to clone
            return
        elif response.status_code != 200:
            raise GitHubError(f"GitHub API error: {response.status_code}")

        data = response.json()
        if data.get("private", False):
            raise PrivateRepoError(
                f"Repository '{repo.owner}/{repo.name}' is private. "
                "Pycasso-ai can only access public repositories."
            )

    except httpx.TimeoutException:
        raise GitHubError("Timed out checking repository accessibility")
    except httpx.RequestError as e:
        raise GitHubError(f"Network error checking repository: {e}")


def clone_repo(repo: GitHubRepo, target_dir: Path | None = None) -> Path:
    """Clone a GitHub repository to a temporary directory.

    Args:
        repo: Parsed GitHub repository information
        target_dir: Optional target directory. If None, creates a temp directory.

    Returns:
        Path to the cloned repository
    """
    if target_dir is None:
        target_dir = Path(tempfile.mkdtemp(prefix=f"pycasso-{repo.name}-"))

    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo.clone_url, str(target_dir)],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise GitHubError(f"Failed to clone repository: {result.stderr.strip()}")

        return target_dir

    except subprocess.TimeoutExpired:
        raise GitHubError("Clone operation timed out (120s limit)")
    except FileNotFoundError:
        raise GitHubError("git command not found. Please install git.")


def cleanup_repo(repo_path: Path) -> None:
    """Remove a cloned repository directory."""
    try:
        shutil.rmtree(repo_path)
    except OSError:
        pass  # Best effort cleanup
