# Run Your First Model Evaluation

> Get one saved answer from Qwen3 Coder 30B on your own rented DGX Spark, then end billing.

## Table of Contents

- [Overview](#overview)
- [Instructions](#instructions)
- [Troubleshooting](#troubleshooting)
- [Clean up](#clean-up)

---

## Overview

### Basic idea

The quickest way to find out whether a DGX Spark suits your workload is to send it a few of
your own prompts. This playbook uses the console's Qwen3 Coder 30B preset, which starts with
the model already loaded and served, so there is no serving stack to install and no SSH key
to set up. You run a request from the browser terminal, save the answer, copy it to your
computer and terminate the instance.

### What you'll accomplish

- A running instance serving `qwen3-coder-30b` on port 8888 inside the instance.
- `/workspace/first-response.json` with one answer, copied to your computer.
- The instance terminated, so billing has ended.

### What to know before starting

- Basic terminal use.
- Reading JSON output from `curl`.

### Prerequisites

- A GPUwerk account with credit ([console](https://console.gpuwerk.com/deploy)). A deploy
  needs credit for at least one hour, and loading plus testing takes time, so load enough
  for the whole session.
- Optional: an SSH key, if you want to copy files with `scp`
  ([Connect to your instance](../connect-to-your-instance/)).

### Where each step runs

| Label | Meaning |
|---|---|
| **Instance** | In the browser terminal or an SSH session on your GPUwerk instance |
| **Local** | On your own computer |

### Time and risk

- **Duration:** about 15 minutes, plus the time the preset takes to start.
- **Risk level:** Low. Nothing is installed; the only thing to get wrong is leaving the
  instance running.
- **Rollback:** terminate the instance.
- **Cost:** running time is billed per minute at the rate shown in the console;
  see [pricing](https://gpuwerk.com/pricing/).
- **Last updated:** November 24, 2026, first publication.

## Instructions

### Step 1. Write down the test

**Runs on:** Local

Before you deploy, decide what you are measuring. Write down:

- ten prompts that look like your real workload;
- what a correct answer looks like for each;
- the slowest response time you would accept.

Send one request at a time at first. A coding model passing this test tells you about coding
prompts, not about every document or chat workload.

**Expected result:** a short list you can run against the Spark and against your current
model or provider.

### Step 2. Deploy the preset

**Runs on:** the console

1. Open the [console](https://console.gpuwerk.com), sign in and add credit.
2. Choose one Spark and the **Qwen3 Coder 30B** preset. Check the billing conditions and
   availability shown, then deploy.
3. Optional: paste your **public** SSH key if you want SSH or `scp` later. The browser
   terminal works without one.
4. Wait until the status is **running**. The console runs a small inference check first, and
   usage billing starts when it passes.

Credit is prepaid; it does not book or reserve a machine.

**Expected result:** the instance appears with a preparing status, then shows **running**.

### Step 3. Open a terminal

**Runs on:** the console

Open the instance and click **Open terminal in browser**, or use the SSH command shown on
the instance page if you added a key.

**Expected result:** a root prompt on the instance.

### Step 4. List the served model

**Runs on:** Instance

The preset serves the model on port 8888 inside the instance.

```bash
curl --fail --max-time 30 http://127.0.0.1:8888/v1/models
```

**Expected result:** JSON listing one model, `qwen3-coder-30b`.

### Step 5. Send one prompt and save the answer

**Runs on:** Instance

Write the answer to `/workspace`, the part of the instance that survives a rebuild.

```bash
curl --fail --max-time 180 http://127.0.0.1:8888/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen3-coder-30b","messages":[{"role":"user","content":"Write a Python function that returns the unique items in a list, preserving order."}],"max_tokens":256,"temperature":0}' \
  -o /workspace/first-response.json
cat /workspace/first-response.json
```

**Expected result:** a JSON response whose `choices[0].message.content` holds a Python
function.

The preset also publishes the model as an HTTPS endpoint on the internet, protected by an API
key with the `inference` scope. Calling `127.0.0.1` from inside the instance does not switch
that endpoint off. Read the endpoint notes in the [vLLM playbook](../vllm/) before you send
anything confidential.

### Step 6. Run your own prompts and compare

**Runs on:** Instance

Replace the prompt in Step 5 with the ten from Step 1, one at a time, and save each answer
under a new file name. Run the same prompts against your current model or provider. For each,
record correctness, response time, prompt and output length, model configuration and compute
cost, and keep concurrency the same on both sides.

The [benchmark results](https://gpuwerk.com/docs/benchmarks/) are reference workloads, not a
prediction for your prompts.

**Expected result:** a side-by-side record you can judge against the criteria from Step 1.

### Step 7. Copy the results to your computer

**Runs on:** Local

For a small file, select the `cat` output in the browser terminal and paste it into a local
file. With an SSH key and the `spark` alias from
[Connect to your instance](../connect-to-your-instance/), copy it instead:

```bash
scp spark:/workspace/first-response.json ./first-response.json
```

**Expected result:** the local file opens and is complete. For more files and other methods,
see [Get your files out](../get-your-files-out/).

### Step 8. Terminate the instance

**Runs on:** the console

Terminate the instance and type its name to confirm.

**Expected result:** the status shows **terminated** and compute billing ends.

Stop is not the same as terminate: a stopped instance stays held for you and keeps billing.
Terminate deletes the workspace, and GPUwerk keeps no backup you can restore from.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `curl: (7) Failed to connect` / connection refused | The model is still loading | Wait until the console shows **running**, then retry. Do not launch a second paid instance over a timeout |
| `curl: (22) The requested URL returned error: 404` on the completion | The `model` in the request differs from the served name | Use the ID that `/v1/models` returned |
| `curl: (28) Operation timed out` on the completion | A long answer took longer than `--max-time` | Raise `--max-time` or lower `max_tokens` |
| `scp: Permission denied (publickey)` | No SSH key on the instance | Copy the `cat` output from the browser terminal, or add a key ([Connect to your instance](../connect-to-your-instance/)) |

## Clean up

- Copy anything you want to keep off `/workspace` first
  ([Get your files out](../get-your-files-out/)).
- Terminate the instance in the console when you are done; billing ends and the
  workspace is deleted.

## Further reading

- [Your first model evaluation on a rented DGX Spark](https://gpuwerk.com/docs/first-evaluation/)
- [Benchmarks: what to actually expect](https://gpuwerk.com/docs/benchmarks/)
- [The tenant environment](https://gpuwerk.com/docs/tenant-environment/)
- [Serve Models with vLLM](../vllm/) and [Serve Models with llama.cpp](../llama-cpp/), for
  models other than the preset
