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
COPY . /workspaces/gai-mace/src/gai/mace/node
COPY ./persona /root/.gai/persona
COPY ./gai.yml /root/.gai/gai.yml

# Step 4: Install GAI
WORKDIR /workspaces/gai-mace/src/gai/mace/node
RUN pip install -e .

# Step 5: Run GAI
CMD bash -c "python main.py --persona=${GAIMACE_PERSONA}"


