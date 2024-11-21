# COPY TO VOLUME
GAI_CONFIG="${HOME}/.gai/gai.yml"
if [ ! -f ${GAI_CONFIG} ]; then
    cp gai.yml ${GAI_CONFIG}
fi

GAI_PERSONA="${HOME}/.gai/persona/nodes"
if [ ! -d ${GAI_PERSONA} ]; then
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
cd demo
yarn
