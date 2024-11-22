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
ARG CACHE_BUST="0.0.2"
COPY ./gai-mace /workspaces/gai-mace
COPY ./gai-persona /workspaces/gai-persona
COPY ./pyproject.toml /workspaces/pyproject.toml
WORKDIR /workspaces
RUN pip install -e .

# When volume is not mounted, these settings will be used as the node settings.
# When volume is mounted, these settings will be overriden by the user settings.
COPY ./gai.yml /root/.gai/gai.yml
COPY ./gai-mace/src/gai/mace/node/persona/data /root/.gai/persona/nodes

# Step 4: Run GAI
WORKDIR /workspaces/gai-mace/src/gai/mace
CMD bash -c "python main.py"


