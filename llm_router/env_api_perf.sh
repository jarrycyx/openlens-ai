source .env
python llm_router/api_perf.py --api-key $OPENAI_API_KEY \
    --model $MODEL \
    --base-url $BASE_URL \
    --num-requests 8 \
    --max-workers 4 \
    --prompt "请写一篇长文，详细介绍什么是人工智能"