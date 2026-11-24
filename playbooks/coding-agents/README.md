# Point a Coding Agent at Your Spark

> Continue, Cline and aider sending their requests to a model on your own rented DGX Spark.

## Table of Contents

- [Overview](#overview)
- [Instructions](#instructions)
- [Troubleshooting](#troubleshooting)
- [Clean up](#clean-up)

---

## Overview

### Basic idea

Continue, Cline and aider all speak OpenAI's API shape, so each one needs only a base URL, a
key and a model name. This playbook gets an OpenAI-compatible endpoint running on your
instance, keeps it private with an SSH tunnel, and points each agent at it. The code you
send to the agent then goes to a machine you rent, not to a third-party model provider.

### What you'll accomplish

- A model server on your instance answering `GET /v1/models`.
- An SSH tunnel that makes it available as `http://localhost:8888/v1` on your computer.
- Continue, Cline or aider configured to use it.

### What to know before starting

- Basic terminal use and editing a YAML file.
- Which agent you want to use, already installed.

### Prerequisites

- A GPUwerk account with credit, and a running instance with an OpenAI-compatible endpoint:
  a console model preset such as Qwen3 Coder 30B, or your own engine on DGX OS 7 or
  Ubuntu 24.04 ([console](https://console.gpuwerk.com/deploy)).
- For a console preset: an API key with the `inference` scope, created in the console.
- For the tunnel: an SSH key on the instance
  ([Connect to your instance](../connect-to-your-instance/)).
- Continue, Cline or aider on your computer.

### Where each step runs

| Label | Meaning |
|---|---|
| **Instance** | In the browser terminal or an SSH session on your GPUwerk instance |
| **Local** | On your own computer |

### Time and risk

- **Duration:** about 15 minutes with a preset, longer if you download a model yourself.
- **Risk level:** Low. An engine bound to `0.0.0.0` without a key is open to the internet;
  this playbook binds to `127.0.0.1`.
- **Rollback:** remove the provider entry from the agent's config; terminate the instance.
- **Cost:** running time is billed per minute at the rate shown in the console;
  see [pricing](https://gpuwerk.com/pricing/).
- **Last updated:** November 24, 2026, first publication.

## Instructions

### Step 1. Get an endpoint running

**Runs on:** Instance

Choose one:

- **Console model preset.** The model server listens on port 8888 inside the instance. We
  also publish it as an HTTPS endpoint, shown on the instance page and shaped like
  `https://app-<instance-id>.gpuwerk.com`, which needs your inference-scope key as a bearer
  token. Nothing to start.
- **Your own engine.** Use [llama.cpp](../llama-cpp/) if it is just you, since it is faster
  for a single stream, or [vLLM](../vllm/) if several people will share it. Bind it to
  `127.0.0.1` on port 8888 so the steps below match. With llama.cpp:

```bash
llama-server -m /workspace/models/my-model.gguf \
  --host 127.0.0.1 --port 8888 --jinja
```

`--jinja` uses the model's chat template, which llama.cpp needs to return tool calls. To keep
the server running after you disconnect or restart, see
[Keep services running](../keep-services-running/).

**Expected result:** on the instance,
`curl http://127.0.0.1:8888/v1/models` returns JSON whose `data` list contains the model ID.

### Step 2. Open a tunnel to the endpoint

**Runs on:** Local

The tunnel is encrypted end to end and keeps the server off the public internet. Leave it
running while you work:

```bash
ssh -N -L 8888:127.0.0.1:8888 spark
```

(`spark` is the host alias from [Connect to your instance](../connect-to-your-instance/);
use `root@<instance-name>.gpuwerk.com` if you skipped it.)

**Expected result:** in another local terminal,
`curl http://localhost:8888/v1/models` returns the same JSON. Copy the model ID exactly: on
the Qwen3 Coder 30B preset it is `qwen3-coder-30b`. Every config below uses it.

If you would rather use a preset's HTTPS endpoint without SSH, replace
`http://localhost:8888/v1` below with `https://app-<instance-id>.gpuwerk.com/v1` and use your
inference-scope key as the API key:

```bash
curl https://app-<instance-id>.gpuwerk.com/v1/models \
  -H "Authorization: Bearer $GPUWERK_API_KEY"
```

### Step 3. Configure Continue (VS Code or JetBrains)

**Runs on:** Local

Open Continue's `config.yaml` (older installs use `config.json`) and add an entry under
`models`:

```yaml
models:
  - name: My Spark
    provider: openai
    model: qwen3-coder-30b
    apiBase: http://localhost:8888/v1
    apiKey: <your inference-scope key>
```

Set `model` to the ID from Step 2. Over the tunnel to your own engine without a key, any
non-empty `apiKey` value works.

**Expected result:** after you reload the editor window, **My Spark** appears in Continue's
model selector, and a test prompt gets a streamed answer.

### Step 4. Configure Cline (VS Code)

**Runs on:** Local

1. Open Cline's settings and choose the **OpenAI Compatible** provider.
2. Set the base URL to `http://localhost:8888/v1`.
3. Paste your inference-scope key. For your own engine without a key, any non-empty string
   works.
4. Enter the model ID exactly as `/v1/models` reports it.

Cline runs longer tool-use chains and edits more files per turn than Continue, so it uses
more context. Serve the model with a context window that fits your repository.

**Expected result:** a first task shows Cline reading files and answering from your instance.

### Step 5. Configure aider (terminal)

**Runs on:** Local

aider reads the endpoint from environment variables:

```bash
export OPENAI_API_BASE=http://localhost:8888/v1
export OPENAI_API_KEY=<your inference-scope key>
aider --model openai/qwen3-coder-30b
```

Keep the `openai/` prefix in front of the model ID. It tells aider which API format to
speak; no OpenAI service is involved.

**Expected result:** aider opens a chat prompt and answers from your instance.

### Step 6. Pick the right model

**Runs on:** none, read before you scale up

- Use a coding model rather than a general chat model. Qwen3 Coder 30B is the console
  preset for this. It is a mixture-of-experts model with about 3B active parameters, so it
  answers quickly and leaves most of the Spark's 128 GB free.
- The preset serves it as `qwen3-coder-30b` with a 32,768-token context window. For more
  context, run the model yourself on a base image with a larger context setting.
- The preset does not start vLLM with tool-call parsing. Agents that work through OpenAI
  tool calls get their requests rejected by it. For those, run llama.cpp yourself as in
  Step 1.

**Expected result:** you know whether the preset fits your agent, or whether you need your
own engine. See [which models fit in 128 GB](https://gpuwerk.com/docs/models/) for other
options.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Requests fail once a task grows | The prompt passed the server's context limit | Raise the context length on your own engine, or keep tasks smaller on the preset's 32,768 tokens |
| Every response hangs, then arrives at once | A gateway or proxy between agent and engine buffers Server-Sent Events | Turn off response buffering on the proxy |
| 404 that looks like a network problem | The model name in the config does not match the loaded model | Copy the ID from `/v1/models` exactly |
| 401 or 403 from a preset's HTTPS endpoint | Missing or wrong key | Use an API key with the `inference` scope from the account that owns the instance |
| Tool-call requests rejected | The preset runs without tool-call parsing | Run llama.cpp with `--jinja` on a base image (Step 1) |
| `Connection refused` on `localhost:8888` | The tunnel is not running, or nothing listens on 8888 on the instance | Restart the `ssh -N -L` command; check `ss -tlnp` on the instance |

## Clean up

- Stop the tunnel with Ctrl+C, and switch the agent back to another provider if you like.
- Copy anything you want to keep off `/workspace` first
  ([Get your files out](../get-your-files-out/)).
- Terminate the instance in the console when you are done; billing ends and the
  workspace is deleted.

## Further reading

- [Coding agents against your own endpoint](https://gpuwerk.com/docs/coding-agents/)
- [Which models fit in 128 GB](https://gpuwerk.com/docs/models/)
- [Put a gateway in front for keys and budgets](https://gpuwerk.com/docs/litellm/)
- [Continue: config.yaml reference](https://docs.continue.dev/reference)
- [Cline documentation](https://docs.cline.bot/)
- [aider: OpenAI-compatible APIs](https://aider.chat/docs/llms/openai-compat.html)
- [llama.cpp server](https://github.com/ggml-org/llama.cpp/tree/master/tools/server)
- Related playbooks: [llama.cpp](../llama-cpp/), [vLLM](../vllm/),
  [First model evaluation](../first-model-evaluation/), [Inference API](../inference-api/)
