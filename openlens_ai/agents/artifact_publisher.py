import os
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger
from langgraph.graph import StateGraph, START, END

from ..state import State, track_node_call
from ..utils.config import Config

import re

try:
    import requests
except ImportError:
    requests = None


# 认为是“代码/配置相关”的文件后缀
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
    "manuscript",   # 整个 manuscript 不要
    "__pycache__",  # 避免乱七八糟缓存
}

def _get_workspace_dir(config: Config) -> Path:
    """根据当前 Config 推出 workspace 目录。"""
    return Path(config.save_path).expanduser().resolve() / "workspace"


def _collect_code_files(workspace: Path) -> List[Path]:
    files: List[Path] = []
    for p in workspace.rglob("*"):
        if not p.is_file():
            continue

        # --- 新增：排除指定目录 ---
        if any(ex in p.parts for ex in EXCLUDED_DIRS):
            continue

        # --- 只保留特定后缀 ---
        if p.suffix.lower() in CODE_SUFFIXES:
            files.append(p)

    files.sort()
    return files


def _compute_code_stats(workspace: Path, files: List[Path]) -> Dict[str, Any]:
    """计算一些简单的“代码是否正常”的统计量。"""

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
    根据简单的阈值判断是否“看起来像是正常生成的代码”。

    默认阈值可以通过环境变量覆盖：
      - ARTIFACT_MIN_CODE_FILES (默认 5)
      - ARTIFACT_MIN_CODE_BYTES (默认 1024)
      - ARTIFACT_MIN_PY_FILES   (默认 1)
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
    """在 workspace 里写一个 artifact_manifest.json，方便后续检查。"""
    manifest_path = workspace / "artifact_manifest.json"
    manifest_path.write_text(
        json.dumps(stats, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info(f"Wrote artifact_manifest.json at {manifest_path}")
    return manifest_path


def _run_git_command(args: List[str], cwd: Path) -> None:
    """在指定目录下运行 git 命令，失败时抛异常并打印日志。"""
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
    确保 workspace 是一个 git 仓库，并且设置了 remote 和 branch。
    不会帮你配置 token，只假设你本机已经能正常 git push。
    """
    git_dir = workspace / ".git"
    if not git_dir.exists():
        logger.info(f"No .git directory found under {workspace}, initializing a new repo.")
        _run_git_command(["init"], workspace)
    else:
        logger.info(f".git directory already exists under {workspace}")

    # 尝试设置当前 branch 名称
    try:
        _run_git_command(["branch", "-M", branch], workspace)
    except RuntimeError:
        logger.warning("Failed to rename branch, continuing anyway.")

    # 设置 remote origin
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
    自动决定要用哪个 GitHub 仓库 URL：

    1. 如果环境变量里已经设置了 GITHUB_REPO_URL，直接用它（兼容你现在的模式）；
    2. 否则：
       - 如果没有 GITHUB_TOKEN 或没有 requests，就返回空字符串（上层逻辑会选择 skip push）；
       - 如果有 GITHUB_TOKEN，就调用 GitHub API 自动创建一个新仓库，返回它的 ssh_url/clone_url。
    """

    # 1) 用户手动指定了 repo，就尊重它
    repo_url_env = os.getenv("GITHUB_REPO_URL", "").strip()
    if repo_url_env:
        logger.info(f"Using existing GITHUB_REPO_URL={repo_url_env}")
        return repo_url_env

    # 2) 没指定 repo，就尝试自动创建
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        logger.warning(
            "GITHUB_REPO_URL not set and GITHUB_TOKEN not provided; "
            "cannot auto-create GitHub repo. Will skip git push."
        )
        return ""

    if requests is None:
        logger.warning(
            "python-requests not installed; cannot call GitHub API to create repo. "
            "Please `pip install requests` or set GITHUB_REPO_URL explicitly."
        )
        return ""

    # 3) 决定一个 repo 名字
    prefix = os.getenv("GITHUB_REPO_PREFIX", "openlens-").strip()
    # 优先用 thread_id，否则用 save_path 的最后一段
    thread_id = str(state.get("thread_id") or Path(config.save_path).name)
    safe_thread_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", thread_id)[:80].strip("-")
    repo_name = f"{prefix}{safe_thread_id}" if prefix else safe_thread_id

    logger.info(f"Auto-creating GitHub repo with name={repo_name!r}")

    # 4) 调 GitHub API 创建仓库（默认 private，可通过 env 调整）
    is_private = os.getenv("GITHUB_REPO_PRIVATE", "true").lower() != "false"

    api_url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
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
    构建 LangGraph 子图：
        START -> artifact_package_node -> artifact_publish_node -> END

    这里通过“闭包”的方式把 config 传进节点函数，
    节点函数本身的签名保持为 (state: State)，
    和 track_node_call 的包装器完全兼容。
    """

    logger.info("Building artifact_publisher subgraph (pure Python, no OpenHands).")

    @track_node_call("artifact_publisher")
    def artifact_package_node(state: State) -> State:
        """
        节点 1：
        - 扫描 workspace 下的代码相关文件
        - 做一个简单的 sanity check
        - 写 artifact_manifest.json
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
        节点 2：
        - 如果 sanity check 不通过，直接跳过 push
        - 否则把 workspace 当成 git 仓库，自动 add/commit/push 到 GitHub
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

        # 先确定目标分支
        branch = os.getenv("GITHUB_BRANCH", "main").strip() or "main"

        # 自动决定 / 创建远端仓库
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
                # 先根据 manifest 精确决定要 add 哪些文件
                manifest_path_str = state.get("artifact_manifest_path")
                manifest_files: List[str] = []

                if manifest_path_str:
                    manifest_path = Path(manifest_path_str)
                    try:
                        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
                        # 这里的 "files" 是在 _compute_code_stats 里写进去的相对路径
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
                    # 精确 add：只 add manifest 里列出的那些 code 文件
                    for rel_path in manifest_files:
                        _run_git_command(["add", rel_path], workspace)

                    # 顺便把 manifest 自己也 add 上去（方便复现）
                    _run_git_command(["add", Path(manifest_path_str).name], workspace)

                # commit
                _run_git_command(
                    ["commit", "-m", "Add artifact from OpenLens AI artifact_publisher"],
                    workspace,
                )

            except RuntimeError as e:
                # 如果没有任何变化，commit 会失败，这不是致命错误
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
