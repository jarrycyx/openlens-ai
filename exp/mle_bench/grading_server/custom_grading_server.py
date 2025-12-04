import os
import argparse
from pathlib import Path

from flask import Flask, jsonify, request

from mlebench.grade import validate_submission
from mlebench.registry import registry

app = Flask(__name__)

# 默认值，可以通过命令行参数覆盖
PRIVATE_DATA_DIR = os.getenv("PRIVATE_DATA_DIR", "/private/data")
COMPETITION_ID = None  # 将通过命令行参数设置


def run_validation(submission: Path, data_dir: str) -> str:
    new_registry = registry.set_data_dir(Path(data_dir))
    competition = new_registry.get_competition(COMPETITION_ID)
    is_valid, message = validate_submission(submission, competition)
    return message


@app.route("/validate", methods=["POST"])
def validate():
    submission_file = request.files["file"]
    submission_path = Path("/tmp/submission_to_validate.csv")
    submission_file.save(submission_path)

    try:
        result = run_validation(submission_path, PRIVATE_DATA_DIR)
    except Exception as e:
        # Server error
        return jsonify({"error": "An unexpected error occurred.", "details": str(e)}), 500

    return jsonify({"result": result})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running"}), 200


def main():
    parser = argparse.ArgumentParser(description="Custom grading server with configurable data directory")
    parser.add_argument("--data-dir", type=str, default="/private/data", 
                       help="Path to the private data directory")
    parser.add_argument("--host", type=str, default="0.0.0.0", 
                       help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=5000, 
                       help="Port to bind the server to")
    parser.add_argument("--competition-id", type=str, required=True,
                       help="Competition ID for grading")
    
    args = parser.parse_args()
    
    # 设置全局变量
    global PRIVATE_DATA_DIR, COMPETITION_ID
    PRIVATE_DATA_DIR = args.data_dir
    COMPETITION_ID = args.competition_id
    
    print(f"Starting grading server with data directory: {PRIVATE_DATA_DIR}")
    print(f"Competition ID: {COMPETITION_ID}")
    print(f"Server will be available at http://{args.host}:{args.port}")
    
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
