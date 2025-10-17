
# ### Use proxy if encountered network error
export http_proxy="http://127.0.0.1:7890"
export HTTP_PROXY="http://127.0.0.1:7890"
export https_proxy="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"
export all_proxy="http://127.0.0.1:7890"
export ALL_PROXY="http://127.0.0.1:7890"


docker build -t openlens-ai:gpu-latest \
    -f openlens_ai/tools/openhands_configs/ExpDockerfile_gpu \
    --network=host \
    --progress=plain \
    .


# ### Export docker
# echo "Exporting docker to tar.gz"
# docker save openlens-ai:gpu-latest | gzip > exp/docker/openlens-ai:gpu-latest.tar.gz

# ### Import docker
# gunzip -c exp/docker/openlens-ai:gpu-latest.tar.gz | docker load
