docker build -t agent-med-gpu \
    -f openlens_ai/tools/openhands_configs/ExpDockerfile_gpu \
    --network=host \
    --progress=plain \
    .

# --build-arg all_proxy="http://127.0.0.1:7890/" \
# --build-arg http_proxy="http://127.0.0.1:7890/" \
# --build-arg https_proxy="http://127.0.0.1:7890/" \
docker save agent-med-gpu | gzip > exp/docker/docker.tar.gz

# gunzip -c exp/docker/docker.tar.gz | docker load