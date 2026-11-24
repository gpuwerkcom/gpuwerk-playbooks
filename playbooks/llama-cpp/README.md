# Serve Models with llama.cpp

> Build llama.cpp for the GB10's `sm_121` architecture and serve a GGUF model through an
> OpenAI-compatible endpoint on your DGX Spark.

## Table of Contents

- [Overview](#overview)
- [Instructions](#instructions)
- [Troubleshooting](#troubleshooting)
- [Clean up](#clean-up)

---

## Overview

### Basic idea

llama.cpp is built to serve one user fast; vLLM's continuous batching is built for many
concurrent users. On the DGX Spark's 273 GB/s of memory bandwidth that difference shows up in
single-stream decode. Community benchmarks by user `eugr` in
[the llama.cpp GitHub discussions](https://github.com/ggml-org/llama.cpp/discussions/16578)
measured gpt-oss-120b MXFP4 at roughly 60.5 tokens/second decode under llama.cpp, against
roughly 33.5 tokens/second under vLLM on the same model and hardware. Those are reference
figures, not a prediction for your workload. As a rule of thumb: one interactive user or a
coding assistant, run llama.cpp; a team sharing one endpoint, run [vLLM](../vllm/).

This playbook builds `llama-server` from source with the right CUDA architecture and serves
Qwen3.6-35B-A3B from Hugging Face.

If you only want a llama.cpp endpoint and no build, deploy a console preset instead:
GPT-OSS 120B, Qwen3.6 35B-A3B and Qwen3.8 Flash Next run on llama.cpp with the weights
already staged.

### What you'll accomplish

- `llama-server` built for `sm_121` under `/workspace/llama.cpp`.
- A GGUF model answering `/v1/chat/completions` on port 30000.
- Optionally, speculative decoding with the model's MTP draft head.

### What to know before starting

- Basic terminal use.
- Reading a CMake build log well enough to spot a failure.

### Prerequisites

- A GPUwerk account with credit, and a running instance on a base image (DGX OS or
  Ubuntu 24.04) ([console](https://console.gpuwerk.com/deploy)).
- No SSH key is needed for the build: the browser terminal works. You need one only to reach
  the server from your computer through an SSH tunnel
  ([Connect to your instance](../connect-to-your-instance/)).

### Where each step runs

| Label | Meaning |
|---|---|
| **Instance** | In the browser terminal or an SSH session on your GPUwerk instance |
| **Local** | On your own computer |

### Time and risk

- **Duration:** about 15 minutes for the build, plus the model download.
- **Risk level:** Low. The build stays in `/workspace/llama.cpp`; the packages go into the
  container image.
- **Rollback:** `rm -rf /workspace/llama.cpp`, or terminate the instance.
- **Cost:** running time is billed per minute at the rate shown in the console;
  see [pricing](https://gpuwerk.com/pricing/).
- **Last updated:** November 24, 2026, first publication.

## Instructions

### Step 1. Install the build dependencies

**Runs on:** Instance

You are root inside the instance, so no `sudo` is needed. Packages installed with `apt` are
kept across a restart but not across a rebuild; repeat this step after a rebuild.

```bash
apt update
apt install -y git clang cmake libcurl4-openssl-dev libssl-dev
```

**Expected result:** `cmake --version` and `git --version` print version numbers.

### Step 2. Clone into `/workspace`

**Runs on:** Instance

Only `/workspace` survives a rebuild, so keep the source and the build there.

```bash
git clone https://github.com/ggml-org/llama.cpp /workspace/llama.cpp
cd /workspace/llama.cpp
```

**Expected result:** a `/workspace/llama.cpp` directory with `CMakeLists.txt` in it.

### Step 3. Build for `sm_121`

**Runs on:** Instance

These flags follow [llama.cpp's CUDA build instructions](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md#cuda),
with the GB10's architecture. Only the server target is built.

```bash
cmake -B build -DGGML_NATIVE=ON -DGGML_CUDA=ON -DGGML_CURL=ON -DGGML_RPC=ON \
  -DCMAKE_CUDA_ARCHITECTURES=121a-real
cmake --build build --config Release --target llama-server -j
```

The architecture flag is the part people get wrong. GB10 is Blackwell at compute capability
`sm_121`. A `90` (Hopper) or `120` (desktop Blackwell) copied from another guide builds
without error and then fails to use the GPU correctly or underperforms. Use `121a-real`.

**Expected result:** after 5 to 10 minutes, `ls build/bin/` shows `llama-server`.

### Step 4. Start the server

**Runs on:** Instance

With `-hf`, llama.cpp downloads the GGUF from Hugging Face the first time and reuses it
after. Run the server inside `tmux` so it survives a disconnect.

Each instance has its own public IPv4 address, so a server on `--host 0.0.0.0` is reachable
from the internet. This playbook binds to `127.0.0.1` and reaches the server through an SSH
tunnel. If you need it on the public address, add `--api-key <a-long-random-string>` to
require a bearer key.

```bash
cd /workspace/llama.cpp/build
./bin/llama-server \
  -hf unsloth/Qwen3.6-35B-A3B-MTP-GGUF:UD-Q4_K_XL \
  --host 127.0.0.1 \
  --port 30000
```

By default llama-server tries to fit the model's full context window with room for 4
concurrent requests, and scales down if that does not fit. To serve another GGUF, pass
`--model /path/to/file.gguf` instead of `-hf`; multimodal checkpoints then also need
`--mmproj` pointed at the matching projector file (`-hf` fetches it for you).

**Expected result:** the download progress, then a log that ends with the server listening
on port 30000.

### Step 5. Test the endpoint

**Runs on:** Instance

Large GGUFs take a minute or more to load. The first command returns once the health check
passes; the second sends a real completion.

```bash
# wait for the server to be ready
timeout 900 bash -c 'until curl -sf http://127.0.0.1:30000/health > /dev/null 2>&1; do sleep 5; done'

# a real completion
curl -X POST http://127.0.0.1:30000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "unsloth/Qwen3.6-35B-A3B-MTP-GGUF:UD-Q4_K_XL",
    "messages": [{"role": "user", "content": "Explain KV cache in two sentences."}],
    "max_tokens": 200
  }'
```

**Expected result:** JSON with a `choices` list containing the answer.

### Step 6. Reach it from your computer

**Runs on:** Local

With an SSH key and the `spark` alias from
[Connect to your instance](../connect-to-your-instance/):

```bash
ssh -N -L 30000:127.0.0.1:30000 spark
```

**Expected result:** while the tunnel runs, `http://localhost:30000/v1` is an
OpenAI-compatible base URL on your computer. Point [Open WebUI](../open-webui/),
Continue.dev or any OpenAI client at it.

### Step 7. Optional: speculative decoding with MTP

**Runs on:** Instance

Models that ship an MTP (multi-token prediction) draft head, like the Qwen3.6-35B-A3B-MTP
checkpoint above, can use it for speculative decoding: the server drafts several tokens
ahead and verifies them in one pass. Stop the server from Step 4 (Ctrl+C) and start it with:

```bash
cd /workspace/llama.cpp/build
./bin/llama-server \
  -hf unsloth/Qwen3.6-35B-A3B-MTP-GGUF:UD-Q4_K_XL \
  --host 127.0.0.1 \
  --port 30000 \
  --chat-template-kwargs '{"preserve_thinking": true}' \
  -np 1 \
  --spec-type draft-mtp \
  --spec-draft-n-max 2
```

Check the model card first. Unsloth's card for this GGUF (checked 11 October 2026) uses a
2-token draft and one slot: MTP does not yet work with more than one parallel slot (`-np`) or
with `--mmproj`. `--spec-type draft-mtp` works only with a checkpoint that ships MTP weights.
The `preserve_thinking` flag is unrelated to MTP: it keeps earlier reasoning blocks in the
conversation history, which matters for agent workflows on Qwen's thinking models.

**Expected result:** the server starts as in Step 4, and Step 5 returns an answer.

### Step 8. Set the context length

**Runs on:** Instance

llama.cpp allocates the model's maximum supported context if memory allows; set it yourself
with `--ctx-size`. For coding agents, aim for at least 32,768 tokens and preferably 100,000
or more, because tool calls and file contents use context quickly.

The 128 GB is unified memory that the OS and SSH share with the model. Leave a few gigabytes
of headroom rather than letting `--ctx-size` default to the model's maximum.

```bash
free -g
```

**Expected result:** the "available" column stays well above zero while the server runs.

To start the server automatically after a restart, put it in the startup hook
`/workspace/.gpuwerk-init`; see [Keep services running](../keep-services-running/).

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Server runs but generation is slow or ignores the GPU | Built for `90` or `120` from another guide | Delete `build/` and repeat Step 3 with `121a-real` |
| Server fails to start with `--spec-type draft-mtp` | The checkpoint has no MTP weights, or `-np` is above 1, or `--mmproj` is set | Use an MTP checkpoint, `-np 1`, and no `--mmproj` |
| Health check times out or the process is killed while loading | The context does not fit next to the weights | Set a smaller `--ctx-size` and watch `free -g` |
| `connection refused` on port 30000 from your computer | The server is bound to `127.0.0.1` and no tunnel is running | Start the tunnel in Step 6 |
| Build tools missing after a rebuild | `apt` packages are reinstalled fresh on a rebuild | Repeat Step 1; the build under `/workspace` is still there |

## Clean up

- Stop the server with Ctrl+C and the tunnel with Ctrl+C.
- Copy anything you want to keep off `/workspace` first
  ([Get your files out](../get-your-files-out/)).
- Terminate the instance in the console when you are done; billing ends and the
  workspace is deleted.

## Further reading

- [llama.cpp on a DGX Spark: build, serve, when to pick it](https://gpuwerk.com/docs/llama-cpp/)
- [llama.cpp build documentation](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md)
- [llama-server README](https://github.com/ggml-org/llama.cpp/tree/master/tools/server)
- [Benchmarks: what to actually expect](https://gpuwerk.com/docs/benchmarks/)
- [The tenant environment](https://gpuwerk.com/docs/tenant-environment/)
- [Serve Models with vLLM](../vllm/), [Set Up Open WebUI as a Private Chat](../open-webui/)
