curl -X POST http://127.0.0.1:8077/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-llm",
    "messages": [
      {
        "role": "user",
        "content": "你认为应该如何进行医疗信息学研究，写1000字以上"
      }
    ],
    "stream": false
  }'