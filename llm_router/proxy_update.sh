
# 生成配置文件
python llm_router/create_yaml.py --api-key-files llm_router/keys_0825.txt llm_router/keys_0826.txt --output llm_router/model_list.yaml

litellm --config llm_router/model_list.yaml --port 8077
