docker build -t openlens-ai:cpu-latest \
    -f openlens_ai/tools/openhands_configs/ExpDockerfile_cpu \
    --network=host \
    --progress=plain \
    .


### Use proxy if encountered network error
# docker build -t openlens-ai:cpu-latest \
#     -f openlens_ai/tools/openhands_configs/ExpDockerfile_cpu \
#     --build-arg all_proxy="http://127.0.0.1:7890/" \ 
#     --build-arg http_proxy="http://127.0.0.1:7890/" \
#     --build-arg https_proxy="http://127.0.0.1:7890/" \
#     --network=host \
#     --progress=plain \
#     .

# ### Export docker
# echo "Exporting docker to tar.gz"
# docker save openlens-ai:cpu-latest | gzip > exp/docker/openlens-ai:cpu-latest.tar.gz

# ### Import docker
# gunzip -c exp/docker/openlens-ai:cpu-latest.tar.gz | docker load