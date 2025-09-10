docker build -t agent-med-cpu \
    -f openlens_ai/tools/openhands_configs/ExpDockerfile_cpu \
    --network=host \
    --progress=plain \
    --no-cache \
    .

# --build-arg all_proxy="http://127.0.0.1:7890/" \
# --build-arg http_proxy="http://127.0.0.1:7890/" \
# --build-arg https_proxy="http://127.0.0.1:7890/" \
docker save agent-med-cpu | gzip > exp/docker/docker-cpu.tar.gz

# gunzip -c exp/docker/docker-cpu.tar.gz | docker load