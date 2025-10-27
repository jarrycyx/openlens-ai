


cd openlens_ai/tools/openhands_configs/
# curl https://mirrors.tuna.tsinghua.edu.cn/CTAN/systems/texlive/Images/texlive2025-20250308.iso -o texlive2025-20250308.iso
cd ../../../


# ### Use proxy if encountered network error
export http_proxy="http://127.0.0.1:7890"
export HTTP_PROXY="http://127.0.0.1:7890"
export https_proxy="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"
export all_proxy="http://127.0.0.1:7890"
export ALL_PROXY="http://127.0.0.1:7890"


docker build -t openlens-ai:base-latest \
    -f openlens_ai/tools/openhands_configs/Dockerfile_cpu_base \
    --network=host \
    --progress=plain \
    .


    # --no-cache \



unset http_proxy
unset HTTP_PROXY
unset https_proxy
unset HTTPS_PROXY
unset all_proxy
unset ALL_PROXY