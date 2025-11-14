python llm_router/deploy_model_vllm.py -m /data/models/QuantTrio/GLM-4.6-AWQ -p 8000 -g 0,1,2,3 --max-len 100000 --extra="--enable-expert-parallel --gpu-memory-utilization 0.75 --enforce-eager"

# KAT dev
MODEL_PATH="outputs/unsloth-sft-kat-lr1e-06-qlora32-data-20251107_172711/quantized_model"
vllm serve $MODEL_PATH \
    --max-model-len 100000 \
    --port 8000 \
    --tool-parser-plugin $MODEL_PATH/qwen3coder_tool_parser.py \
    --chat-template $MODEL_PATH/chat_template.jinja \
    --enable-auto-tool-choice \
    --tool-call-parser qwen3_coder \
    --served-model-name llm
