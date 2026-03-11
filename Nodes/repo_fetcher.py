import os
import shutil
import tempfile

import git


def fetch_repo(state):
    repo_url = state["repo_url"]

    # Use /tmp on Vercel (writable); unique dir per invocation to avoid clashes
    repo_path = tempfile.mkdtemp(prefix="student_repo_")
    try:
        git.Repo.clone_from(repo_url, repo_path)
    except Exception:
        shutil.rmtree(repo_path, ignore_errors=True)
        raise

    try:
        parts = []
        for root, _, files in os.walk(repo_path):
            for file in sorted(files):
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    rel_path = os.path.relpath(path, repo_path)
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    parts.append(f"# --- {rel_path} ---\n{content}")
        code = "\n\n".join(parts) if parts else ""
        return {"code": code}
    finally:
        shutil.rmtree(repo_path, ignore_errors=True)