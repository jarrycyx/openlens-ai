
python llm_router/performance_test/api_perf.py --api-key 0 \
    --model llm \
    --base-url http://127.0.0.1:8000/v1 \
    --num-requests 20 \
    --max-workers 4 