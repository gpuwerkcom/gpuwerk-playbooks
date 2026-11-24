# Set Up Open WebUI as a Private Chat

> Put a ChatGPT-style interface with accounts and chat history in front of the model on your
> DGX Spark, reachable only through an SSH tunnel.

## Table of Contents

- [Overview](#overview)
- [Instructions](#instructions)
- [Troubleshooting](#troubleshooting)
- [Clean up](#clean-up)

---

## Overview

### Basic idea

Open WebUI is a web frontend for an OpenAI-compatible endpoint: accounts, chat history,
document upload and model switching, so you and colleagues can use a model without `curl`. It
does no GPU work itself, so it runs inside your instance next to the server that hosts the
model. This playbook installs it with Docker where the instance has Docker and with `pip`
where it does not, connects it to your model, locks down sign-ups and opens it through an
SSH tunnel.

### What you'll accomplish

- Open WebUI listening on `127.0.0.1:8080` inside the instance, with its data in
  `/workspace/open-webui`.
- A connection to your model, visible in the model picker.
- An admin account of your own and sign-ups turned off.
- The interface open at `http://localhost:8080` on your computer.

### What to know before starting

- Basic terminal use.
- SSH port forwarding ([Connect to your instance](../connect-to-your-instance/), Step 6).

### Prerequisites

- A GPUwerk account with credit, and a running instance with an OpenAI-compatible endpoint
  ([console](https://console.gpuwerk.com/deploy)): a console model preset, or your own server
  from [Serve Models with vLLM](../vllm/) or [Serve Models with llama.cpp](../llama-cpp/).
- An SSH key on the instance, because the tunnel runs from your own SSH client
  ([Connect to your instance](../connect-to-your-instance/)). The install commands also work
  in the browser terminal.

### Where each step runs

| Label | Meaning |
|---|---|
| **Instance** | In the browser terminal or an SSH session on your GPUwerk instance |
| **Local** | On your own computer |

### Time and risk

- **Duration:** about 15 minutes.
- **Risk level:** Low, as long as Open WebUI stays on `127.0.0.1`. The first account created
  becomes the admin, so create yours before anyone else can reach the port.
- **Rollback:** stop Open WebUI and delete `/workspace/open-webui`, or terminate the
  instance.
- **Cost:** running time is billed per minute at the rate shown in the console;
  see [pricing](https://gpuwerk.com/pricing/).
- **Last updated:** November 24, 2026, first publication.

## Instructions

### Step 1. Check whether the instance has Docker

**Runs on:** Instance

Docker inside an instance depends on the machine. Many Sparks give the instance its own
Docker daemon; others run a plain container without Docker, and you cannot choose which.

```bash
docker info
```

**Expected result:** a block of daemon information means you have Docker: use Step 2. An
error such as `command not found` or `Cannot connect to the Docker daemon` means you do not:
use Step 3.

### Step 2. With Docker: run the container

**Runs on:** Instance

`--network host` lets the container reach a model server on the instance's `localhost`, and
`HOST=127.0.0.1` keeps Open WebUI off the public address. The data directory is a bind mount
under `/workspace`, so it survives a rebuild and is easy to back up.

```bash
docker run -d \
  --name open-webui \
  --network host \
  -e HOST=127.0.0.1 \
  -e ENABLE_OLLAMA_API=False \
  -v /workspace/open-webui:/app/backend/data \
  --restart unless-stopped \
  ghcr.io/open-webui/open-webui:main
```

With host networking the port is 8080, not the 3000 in the upstream quick start (3000 is the
host side of a `-p 3000:8080` mapping). `ENABLE_OLLAMA_API=False` stops it probing for an
Ollama server you are not running, which otherwise causes a slow page load and an error
toast.

**Expected result:** `docker logs open-webui` shows the server starting, and
`curl -s http://127.0.0.1:8080/health` answers. Continue at Step 4.

### Step 3. Without Docker: install with pip

**Runs on:** Instance

Open WebUI's own docs list `pip install open-webui` and `open-webui serve`. It supports
Python 3.11 and 3.12; Ubuntu 24.04 and DGX OS ship 3.12. Install it into a virtual
environment under `/workspace` so a rebuild does not remove it.

```bash
apt update && apt install -y python3-venv
python3 -m venv /workspace/open-webui-venv
. /workspace/open-webui-venv/bin/activate
python -m pip install open-webui
```

Start it inside `tmux`, with the data directory under `/workspace` and bound to `127.0.0.1`:

```bash
. /workspace/open-webui-venv/bin/activate
DATA_DIR=/workspace/open-webui ENABLE_OLLAMA_API=False \
  open-webui serve --host 127.0.0.1 --port 8080
```

**Expected result:** the log ends with the server listening on `127.0.0.1:8080`, and
`curl -s http://127.0.0.1:8080/health` answers from a second shell.

### Step 4. Open it through an SSH tunnel and create the admin account

**Runs on:** Local

The first account created becomes the admin. Open the tunnel and sign up straight away.

```bash
ssh -N -L 8080:127.0.0.1:8080 spark
```

Open `http://localhost:8080` in your browser and create your account.

**Expected result:** you are signed in as the admin.

### Step 5. Turn off sign-ups

**Runs on:** Local, in the browser

Turn off new user sign-ups in the admin settings. `ENABLE_SIGNUP` is stored in Open WebUI's
database after the first start, so changing the environment variable later has no effect;
the admin settings are the place to change it.

If colleagues should register themselves and wait for approval, leave sign-ups on instead:
new accounts get the `pending` role and can do nothing until an admin approves them.

Do not set `WEBUI_AUTH=False` on anything another person can reach. It turns off login, and
every visitor reads everyone's chat history.

**Expected result:** a private browser window at `http://localhost:8080` shows no way to
create an account.

### Step 6. Connect it to your model

**Runs on:** Local, in the browser

Go to **Settings > Connections** in the admin section and add an OpenAI-compatible
connection:

| Your model server | Base URL | API key |
|---|---|---|
| Console model preset, same instance | `http://localhost:8888/v1` | Any non-empty value; the local path needs none |
| Your own vLLM server | `http://localhost:8000/v1` | Any non-empty value, or the `--api-key` you started it with |
| Your own llama-server | `http://localhost:30000/v1` | Any non-empty value, or the `--api-key` you started it with |

If Open WebUI runs on another server, use the preset's HTTPS endpoint from the console plus
`/v1` (it looks like `https://app-<instance-id>.gpuwerk.com/v1`) and an API key with the
`inference` scope from the account that owns the instance. Keep that key in the Open WebUI
server configuration only.

**Expected result:** after saving, the model picker lists your model, for example
`qwen3-coder-30b`.

### Step 7. Back up the data directory

**Runs on:** Instance

Everything Open WebUI knows lives in `/workspace/open-webui`: the SQLite database with
accounts and chat history, the vector store, uploaded files and the secret key. GPUwerk keeps
no copy of `/workspace`.

```bash
tar czf /workspace/openwebui-$(date +%F).tar.gz -C /workspace open-webui
```

**Expected result:** a dated archive in `/workspace`. Copy it to your computer
([Get your files out](../get-your-files-out/)). To restore, extract it and start Open WebUI
with the same data directory. Take a backup before every upgrade.

To start the pip install after every restart, put the `open-webui serve` command in the
startup hook `/workspace/.gpuwerk-init`; see [Keep services running](../keep-services-running/).

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Empty model picker | Open WebUI's call to `/v1/models` is failing | Test the endpoint from where Open WebUI runs, for example `docker exec open-webui curl -s http://localhost:8000/v1/models`, before changing anything in the UI |
| Slow page load and an Ollama error toast | Open WebUI is probing for Ollama | Set `ENABLE_OLLAMA_API=False` |
| Sign-up button still shown after setting `ENABLE_SIGNUP=False` | The value is already stored in the database | Change it in the admin settings |
| `connection refused` at `http://localhost:8080` | The tunnel is not running, or Open WebUI is still starting | Start the tunnel; check `curl -s http://127.0.0.1:8080/health` on the instance |
| `docker: command not found` | The instance is a plain container without Docker | Use Step 3 |
| pip install fails on Python 3.13 | Open WebUI supports Python 3.11 and 3.12 only | Create the venv with Python 3.12 |
| Users logged out at random behind a load balancer | Each replica generated its own secret key | Set `WEBUI_SECRET_KEY` identically on all replicas (`openssl rand -base64 32`) |

## Clean up

- Stop Open WebUI: `docker rm -f open-webui`, or Ctrl+C in the pip session. Stop the tunnel
  with Ctrl+C.
- Copy anything you want to keep off `/workspace` first
  ([Get your files out](../get-your-files-out/)).
- Terminate the instance in the console when you are done; billing ends and the
  workspace is deleted.

## Further reading

- [Set up Open WebUI on your Spark](https://gpuwerk.com/docs/open-webui/)
- [Open WebUI quick start](https://docs.openwebui.com/getting-started/quick-start/)
- [Open WebUI environment configuration](https://docs.openwebui.com/reference/env-configuration/)
- [The tenant environment: Docker and systemd](https://gpuwerk.com/docs/tenant-environment/#docker)
- [Serve Models with vLLM](../vllm/), [Serve Models with llama.cpp](../llama-cpp/),
  [Connect to your instance](../connect-to-your-instance/)
