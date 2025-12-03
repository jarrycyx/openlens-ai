# test_artifact.py
from pathlib import Path

from openlens_ai.utils.config import Config
from openlens_ai.agents.artifact_publisher import build_artifact_publisher
from openlens_ai.state import State, load_state


def main():
    # 1. 读取配置（注意这里用的是 from_toml，而不是 from_file）
    config = Config.from_toml("config.full-example.toml")

    # 2. 指定一个已经准备好的 workspace 目录
    #    这里请把路径改成你自己刚才放中间结果的那个 workspace 目录
    run_dir = Path("outputs/pred_aki_dy_mimic_icu_csv_20251118173506").resolve()
    if not run_dir.exists():
        raise RuntimeError(f"run_dir 不存在: {run_dir}")
    if not (run_dir / "workspace").exists():
        raise RuntimeError(f"workspace 不存在: {run_dir / 'workspace'}")

    # 2. 用项目自带的 load_state 读取 config 和 state
    #    这样 state 里面会自动带上 save_path、messages 等所有需要的字段
    config, state, last_subgraph = load_state(str(run_dir))

    # 为保险起见，确保 config.save_path 和 state["save_path"] 一致
    config.save_path = str(run_dir)
    state["save_path"] = str(run_dir)

    # 3. 构建 artifact_publisher 子图并执行
    graph = build_artifact_publisher(config)
    final_state: State = graph.invoke(state)

    print("=== artifact_publisher 结束 ===")
    print("artifact_manifest_path:", final_state.get("artifact_manifest_path"))
    print("artifact_code_stats:", final_state.get("artifact_code_stats"))
    print("artifact_ok_to_publish:", final_state.get("artifact_ok_to_publish"))
    print("artifact_published:", final_state.get("artifact_published"))
    print("artifact_repo_url:", final_state.get("artifact_repo_url"))
    print("artifact_logs:")
    for line in final_state.get("artifact_logs", []):
        print("  ", line)


if __name__ == "__main__":
    main()
