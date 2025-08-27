docker build -t agent-med-gpu \
    -f openlens_ai/tools/openhands_configs/ExpDockerfile_gpu \
    --build-arg all_proxy="http://166.111.74.73:17890/" \
    .
