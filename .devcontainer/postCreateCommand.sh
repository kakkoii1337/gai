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
    ipykernel \
    pytest \
    ipykernel \
    nest-asyncio
cd demo
yarn
