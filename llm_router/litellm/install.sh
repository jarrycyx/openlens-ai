
conda create -n llmdeploy python=3.12
conda activate llmdeploy
pip install "litellm[proxy,caching]"
pip install vllm