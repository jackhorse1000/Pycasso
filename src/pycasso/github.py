import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import httpx


@dataclass
class GitHubRepo:
    owner: str
    name: str
    url: str

    @property
    def clone_url(self) -> str:
        return f"https://github.com/{self.owner}/{self.name}.git"

    @property
    def api_url(self) -> str:
        return f"https://api.github.com/repos/{self.owner}/{self.name}"


class GitHubError(Exception):
    pass


class PrivateRepoError(GitHubError):
    pass


GITHUB_URL_PATTERNS = [
    r"^https?://github\.com/[\w.-]+/[\w.-]+",
    r"^github\.com/[\w.-]+/[\w.-]+",
    r"^git@github\.com:[\w.-]+/[\w.-]+",
]

GITHUB_PARSE_PATTERNS = [
    r"https?://github\.com/([\w.-]+)/([\w.-]+)",
    r"github\.com/([\w.-]+)/([\w.-]+)",
    r"git@github\.com:([\w.-]+)/([\w.-]+)",
]


def is_github_url(path_or_url: str) -> bool:
    return any(re.match(pattern, path_or_url) for pattern in GITHUB_URL_PATTERNS)


def parse_github_url(url: str) -> GitHubRepo:
    url = url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]

    for pattern in GITHUB_PARSE_PATTERNS:
        match = re.match(pattern, url)
        if match:
            owner, name = match.groups()
            return GitHubRepo(owner=owner, name=name, url=url)

    raise GitHubError(f"Could not parse GitHub URL: {url}")


def check_repo_public(repo: GitHubRepo) -> None:
    try:
        response = httpx.get(repo.api_url, timeout=10.0)

        if response.status_code == 404:
            raise PrivateRepoError(
                f"Repository '{repo.owner}/{repo.name}' not found or is private. "
                "Pycasso can only access public repositories."
            )
        if response.status_code == 403:
            return
        if response.status_code != 200:
            raise GitHubError(f"GitHub API error: {response.status_code}")

        data = response.json()
        if data.get("private", False):
            raise PrivateRepoError(
                f"Repository '{repo.owner}/{repo.name}' is private. "
                "Pycasso can only access public repositories."
            )

    except httpx.TimeoutException:
        raise GitHubError("Timed out checking repository accessibility")
    except httpx.RequestError as e:
        raise GitHubError(f"Network error checking repository: {e}")


def clone_repo(repo: GitHubRepo, target_dir: Path | None = None) -> Path:
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
    try:
        shutil.rmtree(repo_path)
    except OSError:
        pass
