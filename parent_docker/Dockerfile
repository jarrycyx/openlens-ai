# This Dockerfile enables deploying OpenLens AI with a Docker-in-Docker (DinD) configuration.
# The outer Docker container hosts the environment, and OpenHands executes agent within an inner Docker container.

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    software-properties-common \
    ca-certificates \
    gnupg \
    lsb-release \
    nodejs \
    npm \
    docker.io \
    docker-compose \
    zsh

RUN chsh -s $(which zsh)

WORKDIR /home/openlens

RUN useradd -m -s /bin/bash openlens && \
    usermod -aG docker openlens

RUN wget -O miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash miniconda.sh -b -p /home/openlens/miniconda && \
    rm miniconda.sh

ENV PATH="/home/openlens/miniconda/bin:${PATH}"

RUN conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
RUN conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

RUN conda create -n py312 python=3.12 -y && \
    echo "conda activate py312" >> /home/openlens/.bashrc



# Configure zsh

RUN git clone https://gitee.com/jarrycyx_admin/my-zsh-config.git
RUN cd my-zsh-config && zsh set-zsh.sh

SHELL ["zsh", "-c"]


# Install dependencies
RUN conda run -n py312 pip install --upgrade pip && \
    conda run -n py312 pip install poetry

COPY . /home/openlens/openlens-ai
RUN chown -R openlens:openlens /home/openlens/openlens-ai

WORKDIR /home/openlens/openlens-ai

RUN conda run -n py312 cd modules/file1agent && pip install -e . && \
    conda run -n py312 cd modules/OpenHands && make build && \
    conda run -n py312 pip install -e .

RUN conda run -n py312 streamlit cache clear

USER openlens

ENV PATH="/home/openlens/miniconda/envs/py312/bin:${PATH}"

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["conda", "run", "-n", "py312", "streamlit", "run", "start_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
