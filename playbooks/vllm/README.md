# Serve Models with vLLM

> Get a vLLM server answering OpenAI-compatible requests on your DGX Spark, with memory and
> context flags sized for the GB10's unified memory.

## Table of Contents

- [Overview](#overview)
- [Instructions](#instructions)
- [Troubleshooting](#troubleshooting)
- [Clean up](#clean-up)

---

## Overview

### Basic idea

vLLM is the engine to use once several people share one endpoint: continuous batching lets
concurrent requests share forward passes instead of queueing. For one user at a time,
[llama.cpp](../llama-cpp/) is usually faster on this hardware.

There are two paths. The console's Qwen3 Coder 30B preset runs vLLM with the weights already
staged, so there is nothing to install. For any other Hugging Face model you install vLLM on
a base image yourself, either with the official CUDA 13 container where the instance has
Docker, or natively where it does not.

### What you'll accomplish

- **Preset path:** a working OpenAI-compatible HTTPS endpoint for `qwen3-coder-30b`, tested
  with an API key.
- **Install path:** `vllm serve` running Qwen/Qwen3.8-27B-FP8 (or a model you choose) on
  port 8000, bound to `127.0.0.1`, with weights cached under `/workspace`.

### What to know before starting

- Basic terminal use.
- Python virtual environments, for the native install.
- Roughly how big your model is in memory (parameters times bytes per parameter).

### Prerequisites

- A GPUwerk account with credit, and a running instance
  ([console](https://console.gpuwerk.com/deploy)): the Qwen3 Coder 30B preset for the
  preset path, or a base image (DGX OS or Ubuntu 24.04) for the install path.
- For the preset's HTTPS endpoint: an API key with the `inference` scope, created in the
  console.
- A Hugging Face token if the model you install is gated.
- No SSH key is needed for the commands; the browser terminal works. You need one for an SSH
  tunnel ([Connect to your instance](../connect-to-your-instance/)).

### Where each step runs

| Label | Meaning |
|---|---|
| **Instance** | In the browser terminal or an SSH session on your GPUwerk instance |
| **Local** | On your own computer |

### Time and risk

- **Duration:** about 10 minutes on the preset. On a base image, 30 minutes or more for the
  install, plus the model download.
- **Risk level:** Medium on the install path: a server on `0.0.0.0` is reachable from the
  internet, and an oversized memory setting can get the instance's container restarted.
- **Rollback:** stop the server and delete its directory under `/workspace`, or terminate
  the instance.
- **Cost:** running time is billed per minute at the rate shown in the console;
  see [pricing](https://gpuwerk.com/pricing/).
- **Last updated:** November 24, 2026, first publication.

## Instructions

### Step 1. Preset path: test the endpoint

**Runs on:** Local, or Instance

Skip to Step 3 if you are installing on a base image.

On the Qwen3 Coder 30B preset, vLLM starts with the instance, the weights are mounted
read-only, and the model is served as `qwen3-coder-30b` with a 32,768-token context.

1. Create an API key in the console with only the `inference` scope.
2. Copy the HTTPS endpoint from the instance page. It looks like
   `https://app-<instance-id>.gpuwerk.com`.
3. List the models with the key as a bearer token:

```bash
curl https://app-<instance-id>.gpuwerk.com/v1/models \
  -H "Authorization: Bearer $GPUWERK_API_KEY"
```

For an OpenAI-compatible SDK, use the HTTPS endpoint plus `/v1` as the base URL and your
GPUwerk key as its API key. The gateway checks ownership on every request, and a revoked key
stops working immediately. Keep the key out of frontend JavaScript and URLs.

Inside the instance, the preset also answers at `http://localhost:8888/v1` without the
gateway key.

**Expected result:** JSON whose `data` list contains `qwen3-coder-30b`.

### Step 2. Preset path: decide how you reach it

**Runs on:** Local

The HTTPS endpoint is on the internet, protected by the `inference` key. For confidential
data, use an SSH tunnel to port 8888 instead, which is encrypted end to end:

```bash
ssh -N -L 8888:127.0.0.1:8888 spark
```

**Expected result:** while the tunnel runs, `http://localhost:8888/v1` on your computer
reaches the preset. You are done with the preset path; continue at Step 8 for measurement.

### Step 3. Install path: check whether the instance has Docker

**Runs on:** Instance

Docker inside an instance depends on the machine. Some Sparks run your instance as a system
container with its own Docker daemon; others run a plain container without Docker, and you
cannot choose which.

```bash
docker info
```

**Expected result:** a block of daemon information means you have Docker: use Step 5. An
error such as `command not found` or `Cannot connect to the Docker daemon` means you do not:
use Step 6.

### Step 4. Understand why `pip install vllm` alone fails

**Runs on:** Instance (reading only)

The GB10 is Blackwell at compute capability `sm_121` on an aarch64 host, and that breaks the
obvious install two ways. On aarch64, PyPI dependency resolution has historically pulled a
CPU-only PyTorch, so vLLM installs cleanly and then cannot see the GPU. Even with a
CUDA-enabled PyTorch, `sm_121` kernel support has to be in the build you run, and
FlashInfer's just-in-time compilation for `sm_121` needs CUDA 12.9 or newer, so a build
pinned to CUDA 12.8 fails at load time.

`pip install vllm` in a fresh venv can therefore look successful and still give you a server
that will not start, or one that runs on the CPU at a few tokens per second. Use a CUDA 13
build, in a container or natively.

**Expected result:** you know which check to run if the server later starts on the CPU
(Step 6, item 3).

### Step 5. With Docker: run the CUDA 13 container

**Runs on:** Instance

The vLLM project's [DGX Spark writeup](https://vllm.ai/blog/2026-06-01-vllm-dgx-spark)
recommends the CUDA 13 build of the official server image. Docker on a system container keeps
images in `/workspace/docker`, so they survive a rebuild. Keep the Hugging Face cache under
`/workspace` too, and publish the port on `127.0.0.1` only:

```bash
mkdir -p /workspace/.cache/huggingface
docker run -d --name vllm \
  --gpus all --ipc=host --restart unless-stopped \
  -p 127.0.0.1:8000:8000 \
  -e HF_TOKEN="$HF_TOKEN" \
  -v /workspace/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:cu130-nightly \
  vllm serve Qwen/Qwen3.8-27B-FP8 \
    --gpu-memory-utilization 0.85 \
    --max-model-len 32768 \
    --max-num-seqs 4
docker logs -f vllm
```

`--ipc=host` gives the container the host's shared memory segment; without it, vLLM's
workers fail on larger models. The cache mount means a restart does not download the weights
again.

Pin the tag before you rely on it. `cu130-nightly` moves; once something works, replace it
with the exact release tag or image digest you validated.

**Expected result:** the log ends with the server listening on port 8000. Continue at
Step 7.

### Step 6. Without Docker: install natively

**Runs on:** Instance

On a plain container, install vLLM natively with a CUDA 13 PyTorch build and run the same
`vllm serve` arguments directly. Keep the environment and the cache under `/workspace` so a
rebuild does not remove them.

1. Create a virtual environment and point the Hugging Face cache at `/workspace`:

```bash
apt update && apt install -y python3-venv
python3 -m venv /workspace/vllm-venv
. /workspace/vllm-venv/bin/activate
export HF_HOME=/workspace/.cache/huggingface
```

2. Install a CUDA 13 build of PyTorch for aarch64 using the selector on
   [pytorch.org](https://pytorch.org/get-started/locally/), then vLLM following
   [vLLM's GPU installation guide](https://docs.vllm.ai/en/latest/getting_started/installation/gpu.html).
   Both projects change their install commands often, so take them from those pages rather
   than from an older guide. Cap compiler parallelism while you build:

```bash
export MAX_JOBS=4
export TORCHINDUCTOR_COMPILE_THREADS=4
```

3. Check that PyTorch sees the GPU before you start vLLM:

```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_capability())"
```

4. Start the server in `tmux`, bound to `127.0.0.1`:

```bash
vllm serve Qwen/Qwen3.8-27B-FP8 \
  --host 127.0.0.1 --port 8000 \
  --gpu-memory-utilization 0.85 \
  --max-model-len 32768 \
  --max-num-seqs 4
```

**Expected result:** item 3 prints `True (12, 1)`, and the log ends with the server
listening on port 8000. `False` means a CPU-only PyTorch: reinstall it from the CUDA 13
selection.

### Step 7. Size memory and flags

**Runs on:** Instance

The Spark's 128 GB is shared between CPU and GPU, roughly 121.6 GiB of it addressable.
`--gpu-memory-utilization` is a fraction of total memory, not of free memory, and vLLM
refuses to start if that amount exceeds what is currently free. With 35 GiB already held by
something else, 0.85 asks for 103 GiB, finds 46, and fails. Empty the box rather than
lowering the number to fit around another workload.

The same pool also serves the OS, SSH and any JIT compiler at startup (FlashInfer autotune,
Triton, `torch.compile`). With a JIT-heavy backend, keep `--gpu-memory-utilization` at 0.6
or below; for plain serving, 0.7 is a safer ceiling than 0.85 to 0.9. If an instance goes
over anyway, the platform kills and restarts the instance's container: your files survive
and SSH comes back, but your server does not restart on its own.

Four flags do most of the work:

- `--gpu-memory-utilization`: start at 0.85 on an otherwise empty instance, lower it if the
  server will not start.
- `--max-model-len`: set it to the longest prompt you actually send. The model's full
  advertised length is the most common reason a server refuses to boot.
- `--max-num-seqs`: around 4 for interactive single-user work; raise it for a team.
- `--served-model-name`: a short alias that clients pass as `model`.

On quantization: prefer NVFP4 when a model ships in it, AWQ otherwise. GGUF is a llama.cpp
format; run it under [llama.cpp](../llama-cpp/) instead.

```bash
free -g
```

**Expected result:** with the server loaded, "available" stays above roughly 8 GB.

### Step 8. Verify and measure

**Runs on:** Instance

Confirm the model is loaded and answering before you point anything at it. For the preset,
use port 8888 and the model `qwen3-coder-30b`.

```bash
# what is served, and under what name
curl http://localhost:8000/v1/models

# a real completion
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3.8-27B-FP8",
    "messages": [{"role": "user", "content": "Explain KV cache in two sentences."}]
  }'
```

For throughput, use vLLM's own harness, which separates prefill from decode:

```bash
# with Docker (Step 5)
docker exec -it vllm vllm bench serve \
  --model Qwen/Qwen3.8-27B-FP8 \
  --num-prompts 64 --request-rate 4

# native install (Step 6), in the activated venv
vllm bench serve \
  --model Qwen/Qwen3.8-27B-FP8 \
  --num-prompts 64 --request-rate 4
```

Decode is bandwidth-bound and modest on this hardware; prefill is where the Spark does well.
The [benchmark page](https://gpuwerk.com/docs/benchmarks/) has reference points, which are
not a prediction for your workload.

**Expected result:** the model list, a JSON answer in `choices`, and a benchmark summary.

### Step 9. Keep it private and running

**Runs on:** Instance, then Local

The preset's HTTPS endpoint is protected by GPUwerk's gateway authentication. A server you
start yourself is not: each instance has its own public IPv4 address, so a server on
`0.0.0.0:8000` is reachable from the internet. Keep it on `127.0.0.1` and use an SSH tunnel
(`ssh -N -L 8000:127.0.0.1:8000 spark`), or start it with `--api-key`. A tunnel alone does
not close a port that is already open.

To start the native server after every restart, put the `vllm serve` command in the startup
hook `/workspace/.gpuwerk-init`; see [Keep services running](../keep-services-running/).

**Expected result:** `curl http://<instance-name>.gpuwerk.com:8000/v1/models` from your
computer fails, and the tunnel works.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `docker: command not found` or `Cannot connect to the Docker daemon` | The instance is a plain container without Docker | Use Step 6, or deploy the Qwen3 Coder 30B preset |
| vLLM refuses to start, reporting less free memory than requested | Something else holds memory, or `--gpu-memory-utilization` is too high | Stop the other process; if the box is empty, lower the value |
| Server refuses to boot with a KV cache error | `--max-model-len` is set to the model's full length | Set it to the longest prompt you send |
| Server starts but runs at a few tokens per second | CPU-only PyTorch | Run the check in Step 6, item 3; reinstall PyTorch from the CUDA 13 selection |
| Fails at load time on FlashInfer | Build pinned to CUDA 12.8 | Use a CUDA 13 build |
| Workers crash on a larger model in Docker | `--ipc=host` missing | Recreate the container with `--ipc=host` |
| Server gone, files intact, SSH reconnects | The instance went over memory and its container was restarted | Lower `--gpu-memory-utilization`, cap `MAX_JOBS`, and start the server again |

## Clean up

- Stop the server: `docker rm -f vllm`, or Ctrl+C in the native session.
- Copy anything you want to keep off `/workspace` first
  ([Get your files out](../get-your-files-out/)).
- Terminate the instance in the console when you are done; billing ends and the
  workspace is deleted.

## Further reading

- [Install vLLM on DGX Spark: container, flags and memory math](https://gpuwerk.com/docs/vllm/)
- [The tenant environment: Docker and systemd](https://gpuwerk.com/docs/tenant-environment/#docker)
- [vLLM on DGX Spark (vLLM blog)](https://vllm.ai/blog/2026-06-01-vllm-dgx-spark)
- [vLLM GPU installation](https://docs.vllm.ai/en/latest/getting_started/installation/gpu.html)
- [Benchmarks: what to actually expect](https://gpuwerk.com/docs/benchmarks/)
- [Serve Models with llama.cpp](../llama-cpp/), [Set Up Open WebUI as a Private Chat](../open-webui/)
