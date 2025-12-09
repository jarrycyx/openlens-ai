import os
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger
from langgraph.graph import StateGraph, START, END

from ..state import State, track_node_call, load_state
from ..utils.config import Config

import re

try:
    import requests
except ImportError:
    requests = None


# File suffixes considered as "code/configuration related"
CODE_SUFFIXES = {
    ".py",
    ".ipynb",
    ".sh",
    ".bat",
    ".ps1",
    ".yaml",
    ".yml",
    ".toml",
    ".txt",
}

EXCLUDED_DIRS = {
    "manuscript",   # Exclude the entire manuscript directory
    "__pycache__",  # Avoid messy cache files
}

def _get_workspace_dir(config: Config) -> Path:
    """Derive workspace directory from current Config."""
    return Path(config.save_path).expanduser().resolve() / "workspace"


def _collect_code_files(workspace: Path) -> List[Path]:
    files: List[Path] = []
    for p in workspace.rglob("*"):
        if not p.is_file():
            continue

        # --- New: Exclude specified directories ---
        if any(ex in p.parts for ex in EXCLUDED_DIRS):
            continue

        # --- Only keep files with specific suffixes ---
        if p.suffix.lower() in CODE_SUFFIXES:
            files.append(p)

    files.sort()
    return files


def _compute_code_stats(workspace: Path, files: List[Path]) -> Dict[str, Any]:
    """Calculate simple statistics to check if code looks normal."""

    total_bytes = 0
    py_files = 0
    ipynb_files = 0

    for p in files:
        try:
            size = p.stat().st_size
        except OSError:
            size = 0
        total_bytes += size
        if p.suffix == ".py":
            py_files += 1
        if p.suffix == ".ipynb":
            ipynb_files += 1

    stats: Dict[str, Any] = {
        "workspace": str(workspace),
        "code_file_count": len(files),
        "total_bytes": total_bytes,
        "py_file_count": py_files,
        "ipynb_file_count": ipynb_files,
        "files": [p.relative_to(workspace).as_posix() for p in files],
    }
    return stats


def _decide_ok_to_publish(stats: Dict[str, Any]) -> bool:
    """
    Determine if it "looks like normally generated code" based on simple thresholds.

    Default thresholds can be overridden via environment variables:
      - ARTIFACT_MIN_CODE_FILES (default 5)
      - ARTIFACT_MIN_CODE_BYTES (default 1024)
      - ARTIFACT_MIN_PY_FILES   (default 1)
    """

    min_files = int(os.getenv("ARTIFACT_MIN_CODE_FILES", "5"))
    min_bytes = int(os.getenv("ARTIFACT_MIN_CODE_BYTES", "1024"))
    min_py = int(os.getenv("ARTIFACT_MIN_PY_FILES", "1"))

    file_count = stats.get("code_file_count", 0)
    total_bytes = stats.get("total_bytes", 0)
    py_files = stats.get("py_file_count", 0)

    ok = True
    reasons: List[str] = []

    if file_count < min_files:
        ok = False
        reasons.append(f"code_file_count={file_count} < {min_files}")
    if total_bytes < min_bytes:
        ok = False
        reasons.append(f"total_bytes={total_bytes} < {min_bytes}")
    if py_files < min_py:
        ok = False
        reasons.append(f"py_file_count={py_files} < {min_py}")

    if not ok:
        logger.warning("Artifact sanity check failed: " + "; ".join(reasons))
    else:
        logger.info(
            f"Artifact sanity check passed: files={file_count}, "
            f"bytes={total_bytes}, py_files={py_files}"
        )

    stats["sanity_ok"] = ok
    stats["sanity_reasons"] = reasons
    return ok


def _write_manifest(workspace: Path, stats: Dict[str, Any]) -> Path:
    """Write an artifact_manifest.json in workspace for later inspection."""
    manifest_path = workspace / "artifact_manifest.json"
    manifest_path.write_text(
        json.dumps(stats, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info(f"Wrote artifact_manifest.json at {manifest_path}")
    return manifest_path


def _run_git_command(args: List[str], cwd: Path) -> None:
    """Run git command in specified directory, throw exception and log on failure."""
    logger.debug(f"Running git command in {cwd}: {' '.join(['git'] + args)}")
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.error(f"git {' '.join(args)} failed with code {result.returncode}")
            logger.error(f"stdout:\n{result.stdout}")
            logger.error(f"stderr:\n{result.stderr}")
            raise RuntimeError(f"git {' '.join(args)} failed")
        if result.stdout:
            logger.debug(f"git stdout:\n{result.stdout}")
        if result.stderr:
            logger.debug(f"git stderr:\n{result.stderr}")
    except Exception as e:
        msg = f"[artifact_publish_node] Failed to publish artifact: {e}"
        logger.error(msg)

def _ensure_git_repo(workspace: Path, repo_url: str, branch: str) -> None:
    """
    Ensure workspace is a git repository with remote and branch configured.
    Won't configure token for you, only assumes your local machine can git push normally.
    """
    git_dir = workspace / ".git"
    if not git_dir.exists():
        logger.info(f"No .git directory found under {workspace}, initializing a new repo.")
        _run_git_command(["init"], workspace)
    else:
        logger.info(f".git directory already exists under {workspace}")

    # Try to set current branch name
    try:
        _run_git_command(["branch", "-M", branch], workspace)
    except RuntimeError:
        logger.warning("Failed to rename branch, continuing anyway.")

    # Set remote origin
    remotes_result = subprocess.run(
        ["git", "remote"],
        cwd=str(workspace),
        capture_output=True,
        text=True,
    )
    existing_remotes = remotes_result.stdout.strip().splitlines()
    if "origin" in existing_remotes:
        logger.info("Remote 'origin' already exists, updating its URL.")
        _run_git_command(["remote", "set-url", "origin", repo_url], workspace)
    else:
        logger.info("Adding remote 'origin'.")
        _run_git_command(["remote", "add", "origin", repo_url], workspace)

def _auto_create_github_repo_if_needed(state: State, config: Config) -> str:
    """
    Automatically decide which GitHub repository URL to use:

    Priority:
    1. If Config.git.repo_url has a value: Use it directly (push to fixed repo, no auto-creation);
    2. Otherwise:
       - Use Config.git.token or GITHUB_TOKEN to call GitHub API to auto-create new repo;
       - New repo name is determined by Config.git.repo_prefix + thread_id;
       - private is determined by Config.git.private.
    """

    frontend_config = getattr(config, "frontend", None)
    logger.info(f"frontend_config: {frontend_config}")
    logger.info(f"config.git: {config.git}")

    repo_url_cfg = config.git.repo_url
    repo_url = repo_url_cfg.strip()
    if repo_url:
        logger.info(f"Using existing GitHub repo URL={repo_url}")
        return repo_url

    # 2) If repo_url is not specified, try to auto-create
    token_cfg = config.git.token
    token = token_cfg.strip()
    if not token:
        logger.warning(
            "No GitHub repo URL and no token provided "
            "(Config.git.token / GITHUB_TOKEN both empty); "
            "cannot auto-create GitHub repo. Will skip git push."
        )
        return ""

    # 3) Decide a repo name
    prefix = config.git.repo_prefix.strip()

    thread_id = str(state.get("thread_id") or Path(config.save_path).name)
    safe_thread_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", thread_id)[:80].strip("-")
    repo_name = f"{prefix}{safe_thread_id}" if prefix else safe_thread_id

    logger.info(f"Auto-creating GitHub repo with name={repo_name!r}")

    is_private = config.git.private

    # First get the authenticated user's username
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    
    try:
        user_resp = requests.get("https://api.github.com/user", headers=headers, timeout=15)
        if user_resp.status_code != 200:
            logger.error(f"Failed to get GitHub user info: {user_resp.status_code}")
            return ""
        
        user_data = user_resp.json()
        username = user_data.get("login")
        if not username:
            logger.error("Could not determine GitHub username")
            return ""
    except Exception as e:
        logger.error(f"Failed to get GitHub username: {e}")
        return ""

    # Check if repository already exists
    check_url = f"https://api.github.com/repos/{username}/{repo_name}"
    try:
        resp = requests.get(check_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            # Repository already exists
            data = resp.json()
            ssh_url = data.get("ssh_url")
            https_url = data.get("clone_url")
            repo_url = ssh_url or https_url or ""
            logger.info(f"Using existing GitHub repo {data.get('full_name')} at {repo_url}")
            return repo_url
    except Exception as e:
        logger.debug(f"Failed to check if repo exists: {e}")

    # Repository doesn't exist, create it
    api_url = "https://api.github.com/user/repos"
    payload = {
        "name": repo_name,
        "private": is_private,
        "auto_init": False,
    }

    try:
        resp = requests.post(api_url, headers=headers, json=payload, timeout=15)
    except Exception as e:
        logger.error(f"Failed to call GitHub API to create repo: {e}")
        return ""

    if resp.status_code not in (200, 201):
        logger.error(
            f"GitHub repo creation failed with status={resp.status_code}, body={resp.text}"
        )
        return ""

    data = resp.json()
    ssh_url = data.get("ssh_url")
    https_url = data.get("clone_url")

    repo_url = ssh_url or https_url or ""
    if not repo_url:
        logger.error(f"GitHub API response missing repo URL: {data}")
        return ""

    logger.info(
        f"Created GitHub repo {data.get('full_name')} "
        f"at {repo_url} (private={is_private})"
    )
    return repo_url

def build_artifact_publisher(config: Config) -> StateGraph:
    """
    Build LangGraph subgraph:
        START -> artifact_package_node -> artifact_publish_node -> END

    Here we pass config to node functions through "closure",
    keeping the node function signature as (state: State),
    fully compatible with track_node_call wrapper.
    """

    logger.info("Building artifact_publisher subgraph (pure Python, no OpenHands).")

    @track_node_call("artifact_publisher")
    def artifact_package_node(state: State) -> State:
        """
        Node 1:
        - Scan code-related files under workspace
        - Perform a simple sanity check
        - Write artifact_manifest.json
        """
        logger.info("Running artifact_package_node (code scan + sanity check).")

        workspace = _get_workspace_dir(config)
        workspace.mkdir(parents=True, exist_ok=True)

        code_files = _collect_code_files(workspace)
        logger.info(f"Collected {len(code_files)} code-related files under workspace.")

        stats = _compute_code_stats(workspace, code_files)
        ok_to_publish = _decide_ok_to_publish(stats)
        manifest_path = _write_manifest(workspace, stats)

        state["artifact_manifest_path"] = str(manifest_path)
        state["artifact_code_stats"] = stats
        state["artifact_ok_to_publish"] = ok_to_publish

        logs: List[str] = list(state.get("artifact_logs", []))
        logs.append(
            f"[artifact_package_node] code_files={stats['code_file_count']}, "
            f"bytes={stats['total_bytes']}, py_files={stats['py_file_count']}, "
            f"ok_to_publish={ok_to_publish}."
        )
        state["artifact_logs"] = logs

        return state

    @track_node_call("artifact_publisher")
    def artifact_publish_node(state: State) -> State:
        """
        Node 2:
        - If sanity check fails, skip push directly
        - Otherwise treat workspace as git repo, automatically add/commit/push to GitHub
        """
        logger.info("Running artifact_publish_node (git push).")
        workspace = _get_workspace_dir(config)

        logs: List[str] = list(state.get("artifact_logs", []))
        ok_to_publish = bool(state.get("artifact_ok_to_publish", False))

        if not ok_to_publish:
            msg = (
                "[artifact_publish_node] artifact_ok_to_publish is False; "
                "skip git push to avoid publishing incomplete/empty artifacts."
            )
            logger.warning(msg)
            logs.append(msg)
            state["artifact_logs"] = logs
            state["artifact_published"] = False
            return state

        # First determine target branch
        # First determine target branch (Config.git.branch takes priority, then environment variable)
        config.git = getattr(config, "git", None)
        branch_cfg = (config.git.branch if config.git else None) or ""
        branch = (branch_cfg or "main").strip()

        # Automatically decide/create remote repository
        repo_url = _auto_create_github_repo_if_needed(state, config)

        if not repo_url:
            msg = (
                "[artifact_publish_node] No GitHub repo URL available "
                "(neither GITHUB_REPO_URL set nor auto-creation succeeded); "
                "skip git push."
            )
            logger.warning(msg)
            logs.append(msg)
            state["artifact_logs"] = logs
            state["artifact_published"] = False
            state["artifact_repo_url"] = ""
            return state


        try:
            _ensure_git_repo(workspace, repo_url, branch)

            # add & commit
            try:
                # First precisely decide which files to add based on manifest
                manifest_path_str = state.get("artifact_manifest_path")
                manifest_files: List[str] = []

                if manifest_path_str:
                    manifest_path = Path(manifest_path_str)
                    try:
                        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
                        # The "files" here are relative paths written in _compute_code_stats
                        manifest_files = manifest_data.get("files", [])
                    except Exception as e:
                        logger.warning(f"Failed to load artifact_manifest.json: {e}")

                if not manifest_files:
                    logger.warning(
                        "[artifact_publish_node] No files listed in manifest; "
                        "falling back to `git add .`."
                    )
                    _run_git_command(["add", "."], workspace)
                else:
                    # Precise add: only add code files listed in manifest
                    for rel_path in manifest_files:
                        _run_git_command(["add", rel_path], workspace)

                    # Also add manifest itself (for reproducibility)
                    _run_git_command(["add", Path(manifest_path_str).name], workspace)

                # commit
                _run_git_command(
                    ["commit", "-m", "'Add artifact from OpenLens AI artifact_publisher'"],
                    workspace,
                )

            except RuntimeError as e:
                # If there are no changes, commit will fail, this is not a fatal error
                logger.warning(f"git commit failed (possibly no changes): {e}")

            # push
            _run_git_command(["push", "-u", "origin", branch], workspace)
            msg = f"[artifact_publish_node] Successfully pushed workspace to {repo_url} (branch: {branch})."
            logger.info(msg)
            logs.append(msg)
            state["artifact_published"] = True
            state["artifact_repo_url"] = repo_url
        except Exception as e:
            msg = f"[artifact_publish_node] Failed to publish artifact: {e}"
            logger.error(msg)
            logs.append(msg)
            state["artifact_published"] = False

        state["artifact_logs"] = logs
        return state

    graph_builder = StateGraph(State)
    graph_builder.add_node("artifact_package", artifact_package_node)
    graph_builder.add_node("artifact_publish", artifact_publish_node)

    graph_builder.add_edge(START, "artifact_package")
    graph_builder.add_edge("artifact_package", "artifact_publish")
    graph_builder.add_edge("artifact_publish", END)

    return graph_builder.compile()

if __name__ == "__main__":
    run_dir = Path("outputs/pred_aki_dy_mimic_icu_csv_20251118173506").resolve()
    if not run_dir.exists():
        raise RuntimeError(f"run_dir does not exist: {run_dir}")
    if not (run_dir / "workspace").exists():
        raise RuntimeError(f"workspace does not exist: {run_dir / 'workspace'}")

    config, state, last_subgraph = load_state(str(run_dir))
    config = Config.from_toml("config.temp.toml")

    # For safety, ensure config.save_path and state["save_path"] are consistent
    config.save_path = str(run_dir)
    state["save_path"] = str(run_dir)

    # 3. Build and execute artifact_publisher subgraph
    graph = build_artifact_publisher(config)
    final_state: State = graph.invoke(state)

    print("=== artifact_publisher finished ===")
    print("artifact_manifest_path:", final_state.get("artifact_manifest_path"))
    print("artifact_code_stats:", final_state.get("artifact_code_stats"))
    print("artifact_ok_to_publish:", final_state.get("artifact_ok_to_publish"))
    print("artifact_published:", final_state.get("artifact_published"))
    print("artifact_repo_url:", final_state.get("artifact_repo_url"))
    print("artifact_logs:")
    for line in final_state.get("artifact_logs", []):
        print("  ", line)

