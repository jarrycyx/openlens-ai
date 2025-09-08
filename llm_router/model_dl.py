from modelscope import snapshot_download

# model_id = "Qwen/Qwen3-30B-A3B"
# model_id = "Qwen/Qwen3-4B"
model_id = "Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8"
# model_id = "iic/Whisper-base"
# model_id = "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B"
# model_id = "deepseek-ai/DeepSeek-R1-Distill-Llama-8B"
# model_id = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
# model_id = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"

model_dir = snapshot_download(model_id, cache_dir="/ssd/0/cyx/models")