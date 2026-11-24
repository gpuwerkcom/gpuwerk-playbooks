# Call Open Models with the Inference API

> Send requests to open-weight models with one API key, in the OpenAI or Anthropic format, with no instance to run.

## Table of Contents

- [Overview](#overview)
- [Instructions](#instructions)
- [Troubleshooting](#troubleshooting)
- [Clean up](#clean-up)

---

## Overview

### Basic idea

The GPUwerk Inference API serves open-weight models from DGX Sparks, priced per token and
paid from your account credit. One key works for every model, in the OpenAI format and in
the Anthropic format, so most clients need only a new base URL and key. There is no machine
to rent and nothing to deploy.

### What you'll accomplish

- An API key with the `inference` scope.
- A working request with `curl`, the OpenAI Python SDK and the Anthropic Python SDK.
- An existing tool, such as Open WebUI or LiteLLM, pointed at the API.

### What to know before starting

- Basic terminal use.
- For the SDK examples: Python 3 and `pip`.

### Prerequisites

- A GPUwerk account with credit. Requests are paid from the same balance as rentals.
- No instance and no SSH key.

### Where each step runs

| Label | Meaning |
|---|---|
| **Console** | In the GPUwerk console in your browser |
| **Local** | On your own computer |

### Time and risk

- **Duration:** about 10 minutes.
- **Risk level:** Low. Anyone holding the key can spend your credit, so keep it secret.
- **Rollback:** revoke the key in the console.
- **Cost:** paid per token from your credit. Current models and prices are on the
  [Inference API docs page](https://gpuwerk.com/docs/inference-api/) and the console's
  AI inference page; see also [pricing](https://gpuwerk.com/pricing/).
- **Last updated:** November 24, 2026, first publication.

## Instructions

### Step 1. Create an inference key

**Runs on:** Console

Open [AI inference](https://console.gpuwerk.com/inference) in the console and create an API
key with the `inference` scope. The key is shown once. Store it in an environment variable:

```bash
export GPUWERK_API_KEY=<your key>
```

**Expected result:** `echo $GPUWERK_API_KEY` prints the key in your current shell.

### Step 2. List the models your key can use

**Runs on:** Local

```bash
curl https://api.gpuwerk.com/inference/v1/models \
  -H "Authorization: Bearer $GPUWERK_API_KEY"
```

**Expected result:** JSON listing the available model IDs. The examples below use
`qwen3.6-35b-a3b`; use an ID from this list if it differs.

### Step 3. Send a request in the OpenAI format

**Runs on:** Local

Base URL `https://api.gpuwerk.com/inference/v1`, your key as a bearer token. Chat completions
and completions work, streamed or not.

```bash
curl https://api.gpuwerk.com/inference/v1/chat/completions \
  -H "Authorization: Bearer $GPUWERK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3.6-35b-a3b",
       "messages": [{"role": "user", "content": "Summarise GDPR Article 28 in three bullets."}]}'
```

With the OpenAI Python SDK (`pip install openai`):

```python
import os
from openai import OpenAI

client = OpenAI(base_url="https://api.gpuwerk.com/inference/v1",
                api_key=os.environ["GPUWERK_API_KEY"])

resp = client.chat.completions.create(
    model="qwen3.6-35b-a3b",
    messages=[{"role": "user", "content": "Summarise GDPR Article 28 in three bullets."}],
)
print(resp.choices[0].message.content)
```

**Expected result:** a JSON response with the answer in `choices[0].message.content`. The
model's reasoning comes back separately in `reasoning_content`, not inside the answer.

### Step 4. Send a request in the Anthropic format

**Runs on:** Local

For clients that speak the Anthropic Messages API, the base URL is
`https://api.gpuwerk.com/inference` (without `/v1`) and the key goes in `x-api-key`. With the
Anthropic Python SDK (`pip install anthropic`):

```python
import os
import anthropic

client = anthropic.Anthropic(base_url="https://api.gpuwerk.com/inference",
                             api_key=os.environ["GPUWERK_API_KEY"])

msg = client.messages.create(
    model="qwen3.6-35b-a3b",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Summarise GDPR Article 28 in three bullets."}],
)
print(msg.content[0].text)
```

**Expected result:** the answer printed in your terminal.

### Step 5. Use it from your tools

**Runs on:** Local

Any tool with an OpenAI-compatible provider setting needs three values: base URL
`https://api.gpuwerk.com/inference/v1`, your key, and a model ID from Step 2.

- **Open WebUI:** Admin settings, Connections, add an OpenAI API connection with the base URL
  and key. See [Open WebUI](../open-webui/).
- **LiteLLM:** a model entry with `model: openai/qwen3.6-35b-a3b`, `api_base` and `api_key`.
- **SillyTavern, LibreChat, Jan, n8n** and similar: choose the OpenAI-compatible or custom
  endpoint option and enter the same three values.
- **Coding agents that need native tool calls** will not work yet: the `tools` parameter is
  not supported. Run your own engine instead ([Coding agents](../coding-agents/)).

**Expected result:** the tool lists the model and answers a test prompt.

### Step 6. Know the limits

**Runs on:** none, read before you build on it

- Each account has a requests-per-minute limit, a limit on requests in flight and a daily
  spending limit (per UTC day). The console shows your current limits.
- Capacity varies and there is no service level agreement. Batch jobs that can retry later
  suit the API best.
- Prompt caching is automatic: a repeated prompt prefix is charged at the cached rate.
- Prompts and completions are held in memory while a request runs. They are not stored,
  logged or used for training. Billing records hold the time, model and token counts, never
  content.
- A request may run on a Spark that GPUwerk owns or on one owned by a hosting partner, which
  may be in another country. The console's AI inference page shows the countries of the
  machines serving requests now, and the
  [Inference API data policy](https://gpuwerk.com/legal/inference-api/) has the details.

**Expected result:** your client handles `429` by waiting for `Retry-After` and retrying.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `402` | Your credit does not cover the most this request could cost | Top up in the console |
| `429` | A limit was reached, or no machine is free right now | Wait for the `Retry-After` time and retry. The request was not queued or charged |
| `401` or `403` | The key is unknown or revoked, lacks the `inference` scope, or is bound to one instance | Create a new key with the `inference` scope in the console |
| Request with `tools` rejected | Native tool calling is not supported yet | Remove `tools`, or run your own engine on an instance |

## Clean up

- Revoke keys you no longer use in the console's AI inference page.
- Remove `GPUWERK_API_KEY` from shell profiles and tool configs you shared.

## Further reading

- [Call open models with one API key](https://gpuwerk.com/docs/inference-api/): current
  models, prices and limits
- [Terms, section 21: Inference API](https://gpuwerk.com/legal/terms/#inference-api)
- [Inference API data policy](https://gpuwerk.com/legal/inference-api/)
- [Set up LiteLLM](https://gpuwerk.com/docs/litellm/)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)
- Related playbooks: [Open WebUI](../open-webui/), [Coding agents](../coding-agents/)
