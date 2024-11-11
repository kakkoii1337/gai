FROM python:3.10-bullseye

# Step 1: Install deps
RUN apt update && apt install -y ffmpeg
ENV PATH="/root/.local/bin:${PATH}"
ENV PERSONA=""
ENV NATS=""
ENV TTT=""
ENV RAG=""

# Step 2: Create config
RUN echo '{"app_dir":"/root/.gai"}' > /root/.gairc

# Step 3: Copy source code
COPY ./gai /workspaces/gai
COPY ./gai-itt/src /workspaces/gai-itt/src
COPY ./gai-lib/src /workspaces/gai-lib/src
COPY ./gai-mace/src /workspaces/gai-mace/src
COPY ./gai-network/src /workspaces/gai-network/src
COPY ./gai-persona/src /workspaces/gai-persona/src
COPY ./gai-rag/src /workspaces/gai-rag/src
COPY ./gai-scripts /workspaces/gai-scripts
COPY ./gai-tti/src /workspaces/gai-tti/src
COPY ./gai-tts/src /workspaces/gai-tts/src
COPY ./gai-ttt/src /workspaces/gai-ttt/src
COPY ./pyproject.toml /workspaces/pyproject.toml

# Step 4: Install GAI
WORKDIR /workspaces
RUN pip install -e .
COPY ./gai/gai.yml /root/.gai/gai.yml
COPY ./gai/data /root/.gai/persona/data

# Step 5: Run GAI
WORKDIR /workspaces/gai-mace/src/gai/mace/server
CMD bash -c "python main.py --persona=${GAIMACE_PERSONA}"


