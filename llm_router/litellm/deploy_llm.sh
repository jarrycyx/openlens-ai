MODEL_PATH="/home/models/Kwaipilot/KAT-Dev"
CUDA_VISIBLE_DEVICES=0,1 vllm serve $MODEL_PATH \
    --max-model-len 90000 \
    --tensor-parallel-size 2 \
    --port 8008 \
    --gpu-memory-utilization 0.9 \
    --enable-auto-tool-choice \
    --served-model-name llm \
    --tool-parser-plugin $MODEL_PATH/qwen3coder_tool_parser.py \
    --chat-template $MODEL_PATH/chat_template.jinja \
    --tool-call-parser qwen3_coder