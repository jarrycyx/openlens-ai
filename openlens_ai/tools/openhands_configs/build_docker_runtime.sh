
# ### Use proxy if encountered network error
export http_proxy="http://127.0.0.1:7890"
export HTTP_PROXY="http://127.0.0.1:7890"
export https_proxy="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"
export all_proxy="http://127.0.0.1:7890"
export ALL_PROXY="http://127.0.0.1:7890"

# running openhands adaptor for the first time will try building the runtime image
cd modules/OpenHands
poetry run python -m openhands.core.main -t "Hi" -i 100 --config-file ../../openlens_ai/tools/openhands_configs/build_config.toml
cd ../../

# ### Export docker
# echo "Exporting docker to tar.gz"
# docker save openlens-ai:runtime-latest | gzip > exp/docker/openlens-ai:runtime-latest.tar.gz

# ### Import docker
# gunzip -c exp/docker/openlens-ai:runtime-latest.tar.gz | docker load

# ### Upload to hub
docker tag openlens-ai:runtime-latest crpi-hbt8nkulkjqjqkie.cn-hangzhou.personal.cr.aliyuncs.com/cyx-docker/openlens-ai:runtime-latest
docker push crpi-hbt8nkulkjqjqkie.cn-hangzhou.personal.cr.aliyuncs.com/cyx-docker/openlens-ai:runtime-latest

unset http_proxy
unset HTTP_PROXY
unset https_proxy
unset HTTPS_PROXY
unset all_proxy
unset ALL_PROXY
