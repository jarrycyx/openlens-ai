
docker build -t openlens-ai:gpu-latest \
    -f openlens_ai/tools/openhands_configs/ExpDockerfile_gpu \
    --network=host \
    --progress=plain \
    .


# ### Use proxy if encountered network error
# docker build -t openlens-ai:gpu-latest \
#     -f openlens_ai/tools/openhands_configs/ExpDockerfile_gpu \
#     --build-arg all_proxy="http://127.0.0.1:7890/" \ 
#     --build-arg http_proxy="http://127.0.0.1:7890/" \
#     --build-arg https_proxy="http://127.0.0.1:7890/" \
#     --network=host \
#     --progress=plain \
#     .

# ### Export docker
# echo "Exporting docker to tar.gz"
# docker save openlens-ai:gpu-latest | gzip > exp/docker/openlens-ai:gpu-latest.tar.gz

# ### Import docker
# gunzip -c exp/docker/openlens-ai:gpu-latest.tar.gz | docker load