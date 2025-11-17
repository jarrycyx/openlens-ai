python llm_router/deploy_model_vllm.py -m /data/models/QuantTrio/GLM-4.6-AWQ -p 8000 -g 0,1,2,3 --max-len 100000 --extra="--enable-expert-parallel --gpu-memory-utilization 0.75 --enforce-eager"

# KAT dev
MODEL_PATH="outputs/unsloth-sft-kat-lr0.0001-qlora32-distill-20251111_143454/checkpoint-1800-fp8"
vllm serve $MODEL_PATH \
    --max-model-len 100000 \
    --port 8000 \
    --tool-parser-plugin $MODEL_PATH/qwen3coder_tool_parser.py \
    --chat-template $MODEL_PATH/chat_template.jinja \
    --enable-auto-tool-choice \
    --tool-call-parser qwen3_coder \
    --served-model-name llm

python deploy_model_vllm.py \
    -m outputs/unsloth-sft-kat-lr0.0001-qlora32-distill-20251111_143454/checkpoint-1800-fp8 \
    -g 2,3 \
    -p 8000,8001