curl --request POST \
  --url http://127.0.0.1:8077/v1/rerank \
  --header "Authorization: Bearer 0" \
  --header "Content-Type: application/json" \
  --data '{
      "model": "bge-reranker-v2-m3",
      "query": "A man is eating pasta.",
      "documents": [
          "A man is eating food.",
          "A man is eating a piece of bread."
      ]
    }'