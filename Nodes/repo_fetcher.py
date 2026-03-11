import os
import re
import shutil
import tempfile
import zipfile
from urllib.request import urlopen, Request

# GitPython only when git binary exists (e.g. local dev); Vercel has no git
try:
    import git
    _GIT_AVAILABLE = True
except Exception:
    _GIT_AVAILABLE = False


def _is_github_url(url):
    return "github.com" in url


def _parse_github_url(url):
    # https://github.com/owner/repo or https://github.com/owner/repo.git
    m = re.match(r"https?://(?:www\.)?github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", url.strip())
    if m:
        return m.group(1), m.group(2)
    return None


def _fetch_via_github_archive(repo_url):
    """Fetch repo as zip from GitHub (no git binary needed; works on Vercel)."""
    parsed = _parse_github_url(repo_url)
    if not parsed:
        raise ValueError("Invalid GitHub URL: " + repo_url)
    owner, repo = parsed

    # Try main then master
    for branch in ("main", "master"):
        zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
        req = Request(zip_url, headers={"User-Agent": "AssignmentEvaluator/1.0"})
        try:
            with urlopen(req, timeout=30) as resp:
                zip_data = resp.read()
        except Exception as e:
            if branch == "master":
                raise RuntimeError(f"Failed to download repo: {e}") from e
            continue
        break
    else:
        raise RuntimeError("Could not download repo (tried main and master)")

    extract_dir = tempfile.mkdtemp(prefix="student_repo_")
    try:
        zip_path = os.path.join(extract_dir, "repo.zip")
        with open(zip_path, "wb") as f:
            f.write(zip_data)
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(extract_dir)
        # Archive has one root folder like repo-main or repo-master
        roots = [d for d in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, d)) and d != "repo.zip"]
        if not roots:
            shutil.rmtree(extract_dir, ignore_errors=True)
            return ""
        repo_path = os.path.join(extract_dir, roots[0])
        return _collect_py_code(repo_path)
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)


def _collect_py_code(repo_path):
    parts = []
    for root, _, files in os.walk(repo_path):
        for file in sorted(files):
            if file.endswith(".py"):
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, repo_path)
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                parts.append(f"# --- {rel_path} ---\n{content}")
    return "\n\n".join(parts) if parts else ""


def fetch_repo(state):
    repo_url = state["repo_url"].strip()

    # GitHub: fetch via archive (no git binary; works on Vercel)
    if _is_github_url(repo_url):
        code = _fetch_via_github_archive(repo_url)
        return {"code": code}

    # Non-GitHub or local: need git binary (fails on Vercel)
    if not _GIT_AVAILABLE:
        raise RuntimeError(
            "Git is not available in this environment (e.g. Vercel). Use a GitHub repo URL (https://github.com/owner/repo)."
        )

    repo_path = tempfile.mkdtemp(prefix="student_repo_")
    try:
        git.Repo.clone_from(repo_url, repo_path)
    except Exception:
        shutil.rmtree(repo_path, ignore_errors=True)
        raise

    try:
        code = _collect_py_code(repo_path)
        return {"code": code}
    finally:
        shutil.rmtree(repo_path, ignore_errors=True)