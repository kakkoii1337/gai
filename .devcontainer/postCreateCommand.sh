# COPY TO VOLUME
GAI_CONFIG="${HOME}/.gai/gai.yml"

# Replace all occurrences of localhost:12031 with gai-ttt-svr:12031
sed -i 's/localhost:12031/gai-ttt-svr:12031/g' "${GAI_CONFIG}"
sed -i 's/localhost:12035/gai-tti-svr:12035/g' "${GAI_CONFIG}"
sed -i 's/localhost:12036/gai-rag-svr:12036/g' "${GAI_CONFIG}"


GAI_PERSONA="${HOME}/.gai/persona/nodes"
if [ ! -d ${GAI_PERSONA} ]; then
    mkdir -p $GAI_PERSONA
    cp -rp gai-mace/src/gai/mace/node/persona/data $GAI_PERSONA
fi

python -m venv ~/.venv
source ~/.venv/bin/activate
pip install -e .
pip install --upgrade \
    pip \
    setuptools \
    wheel \
    build \
    notebook \
    jupyterlab \
    ipywidgets \
    pytest \
    ipykernel \
    nest-asyncio
chmod +x ./demo.sh
cd demo
yarn
