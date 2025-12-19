curl --request POST \
  --url http://127.0.0.1:8077/v1/chat/completions \
  --header "Authorization: Bearer 0" \
  --header "Content-Type: application/json" \
  --data '{
      "model": "mimo-v2-flash",
      "messages": [
        {
          "role": "user",
          "content": "请简要描述图片是什么内容？"
        }
    ],
    "temperature": 0.7,
    "stream": false
  }'