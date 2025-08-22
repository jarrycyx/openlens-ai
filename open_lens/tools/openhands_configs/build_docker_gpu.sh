docker build -t agent-med-gpu \
    -f open_lens/tools/openhands_configs/ExpDockerfile_gpu \
    --build-arg all_proxy="http://166.111.74.73:17890/" \
    .
