# Gaimace: Distributed Multi-Agent Collaborative Environment

The operational costs of autonomous AI agents, primarily driven by the multi-turn, interrogative nature of large language models (LLMs), may eventually pose a significant barrier to their adoption. These costs are further exacerbated by privacy concerns arising from the reliance on external LLM service providers, limiting both cost-efficiency and user control. While the emergence of local LLMs, coupled with the rise in AI-capable consumer hardware, holds the potential to address these challenges by enabling the deployment of AI agents on local hardware—thereby reducing operational costs and privacy risks—most existing multi-agent systems are neither network-ready nor optimized for local LLMs. This limitation hinders the ability to fully leverage the potential of local AI agents for diverse problem-solving scenarios. This paper introduces Gaimace, a generative AI distributed multi-agent collaborative environment designed to be network-ready, local-first, and horizontally scalable. It addresses the need for a system that can utilize local LLMs and AI-capable hardware effectively, ensuring privacy and reducing operational costs. By democratizing the use of AI agents, Gaimace enhances user control and flexibility in diverse problem-solving scenarios.

![network](/docs/img/network.png)

## Pre-Requisites

The following instructions is designed for setting up Gaimace on Windows 11 with WSL2 and Ubuntu 22.04 LTS. The instructions may vary for other operating systems.

To run Gaimace, you need the following pre-requisites:

-   Windows 11
-   WSL2 with Ubuntu 22.04 LTS
-   Docker
-   Visual Studio Code

## Installation

The following instructions are available in video at this youtube [link](https://www.youtube.com/watch?v=3jXOlpO_cjg).

### Step 1. Setup Environment

a) Open WSL2 terminal and create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

b) Install gai-sdk

```bash
pip install gai-sdk
```

c) Initialize Gai directory

```bash
gai init
```

### Step 2. Download and Open Repository

a) Clone gai repository

```bash
git clone https://github.com/kakkoii1337/gai
```

b) Open in Visual Studio Code

```bash
cd gai
code .
```

### Step 3. Open in DevContainer

a) Open **.devcontainer/devcontainer.json** and replace "kakkoii1337" with your username.

For example, if your username is "user1234", replace the field "remoteUser" with "user1234".

b) Open **.devcontainer/docker-compose.yml** and replace "kakkoii1337" with your username.

For example, if your username is "user1234", replace the field "USERNAME" with "user1234".

c) Click on the bottom-left corner on the blue button and select "Reopen in Container"

![Reopen in Container](/docs/img/dev-container.png)

**NOTE:** Docker will pull or build the images required for the devcontainer. This may take approx 10 minutes to complete.

### Step 4. Download Model

a) From Visual Studio Code, open a new terminal and pull the Dolphin model.

**NOTE:** The model is around 4GB+ in size and will take approx 10 min to download.

```bash
gai pull llamacpp-dolphin
```

![gai pull llamacpp-dolphin](/docs/img/gai-pull-llamacpp-dolphin.png)

### Step 5. Start the API Server

a) From Visual Studio Code, Press F5 to start the API server.

### Step 6. Start the Web Server

a) From Visual Studio Code, open a new terminal and start the web server.

```bash
. demo.sh
```

### Step 7. Test and Demo

a) Open a web browser and navigate to http://localhost:5123

b) Type the in the chat box: Hello everyone! Please introduce yourselves and tell me about your capabilities.

c) Click on the "loop" button to fetch group responses.

## Next Step

-   Explore Gaimace Notebooks:
    -   [Geting Started](./docs/01_getting_started.ipynb)
-   [Gaimace Documentation](https://gai.readthedocs.io/en/latest/)
