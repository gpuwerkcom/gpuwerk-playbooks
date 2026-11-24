# <Playbook title: verb + object, for example "Serve Models with llama.cpp">

> <One line: what the reader ends up with.>

## Table of Contents

- [Overview](#overview)
- [Instructions](#instructions)
- [Troubleshooting](#troubleshooting)
- [Clean up](#clean-up)

---

## Overview

### Basic idea

<Two or three sentences: what this playbook sets up and why someone would want it on a
rented DGX Spark.>

### What you'll accomplish

<What is running or produced at the end, in concrete terms.>

### What to know before starting

- <Skills the reader needs, for example "basic terminal use", "Python virtual environments">

### Prerequisites

- A GPUwerk account with credit, and a running instance on <image or preset>
  ([console](https://console.gpuwerk.com/deploy)).
- <Anything else: a Hugging Face token, an SSH key, a local tool>

### Where each step runs

| Label | Meaning |
|---|---|
| **Instance** | In the browser terminal or an SSH session on your GPUwerk instance |
| **Local** | On your own computer |

### Time and risk

- **Duration:** <setup time, plus download or build time>
- **Risk level:** <Low / Medium, and why>
- **Rollback:** <how to undo, usually "terminate the instance">
- **Cost:** running time is billed per minute at the rate shown in the console;
  see [pricing](https://gpuwerk.com/pricing/).
- **Last updated:** <Month DD, YYYY>, <what changed>

## Instructions

### Step 1. <Imperative heading>

**Runs on:** Instance

<What this step does and why, in one or two sentences.>

```bash
<command>
```

**Expected result:** <what the reader should see>.

### Step 2. <…>

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| <error text or behaviour> | <why it happens> | <what to do> |

## Clean up

- Copy anything you want to keep off `/workspace` first
  ([Get your files out](../get-your-files-out/)).
- Terminate the instance in the console when you are done; billing ends and the
  workspace is deleted.

## Further reading

- <Links to the GPUwerk docs page and upstream project docs>
