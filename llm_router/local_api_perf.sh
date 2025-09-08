
python llm_router/api_perf.py --api-key 0 \
    --model llm \
    --base-url http://127.0.0.1:8007 \
    --num-requests 8 \
    --max-workers 4 \
    --prompt "请写一篇长文，详细介绍什么是人工智能"