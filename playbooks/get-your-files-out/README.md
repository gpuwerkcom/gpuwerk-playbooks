# Copy Your Files Off Before You Terminate

> Get results, checkpoints and models off a rented DGX Spark to your own computer or Hugging Face.

## Table of Contents

- [Overview](#overview)
- [Instructions](#instructions)
- [Troubleshooting](#troubleshooting)
- [Clean up](#clean-up)

---

## Overview

### Basic idea

We keep no backup of `/workspace`. Terminating an instance deletes it, and so does a failed
drive. This playbook copies your work off the instance with `scp`, `rsync` or a Hugging Face
upload, checks the copy, and only then terminates.

### What you'll accomplish

- A copy of the folders you need on your own computer, or in a private Hugging Face
  repository.
- A repeatable `rsync` command you can run during a long job.
- A short check that the copy is complete before you terminate.

### What to know before starting

- Basic terminal use.
- For Hugging Face: what a model or dataset repository is.

### Prerequisites

- A running or stopped GPUwerk instance ([console](https://console.gpuwerk.com/deploy)).
- For `scp` and `rsync`: an SSH key added to the instance
  ([Connect to your instance](../connect-to-your-instance/)).
- For Hugging Face: an account and an access token with write access.

The examples use `spark-abcd.gpuwerk.com`. The console's instance page shows your hostname
and SSH command.

### Where each step runs

| Label | Meaning |
|---|---|
| **Instance** | In the browser terminal or an SSH session on your GPUwerk instance |
| **Local** | On your own computer |

### Time and risk

- **Duration:** a few minutes, plus transfer time for large files.
- **Risk level:** Low until Step 6. Terminating cannot be undone.
- **Rollback:** none for a terminated instance. Copy first, terminate last.
- **Cost:** running time is billed per minute at the rate shown in the console;
  see [pricing](https://gpuwerk.com/pricing/).
- **Last updated:** November 24, 2026, first publication.

## Instructions

### Step 1. Know when files are deleted

**Runs on:** none, read first

- **Terminate:** `/workspace` is deleted at once, for good. Billing ends.
- **Stop** from the console: the machine stays held for you and nothing is deleted.
- **Power off from inside** (`poweroff`, `shutdown`): the instance stops but is not
  terminated. If you do not start it again within about 30 minutes, the machine is released
  and the workspace kept on it for up to 48 hours.
- **Credit runs out or your budget is reached:** the instance is stopped and the machine
  released. The workspace stays on it for up to 48 hours, and is deleted sooner if someone
  else rents that machine.
- **A partner Spark is withdrawn or goes offline:** the workspace is kept for 24 hours so you
  can copy it off if the machine is reachable, then wiped.
- **The drive fails:** the workspace is lost. There is no copy.

Only `/workspace` survives a rebuild. Files in `/root`, packages you installed and, on a
system container, units in `/etc/systemd` are not covered by any of the steps below unless
you copy them into `/workspace` or off the instance.

### Step 2. See what you have

**Runs on:** Instance

```bash
du -sh /workspace/* | sort -h
```

**Expected result:** a size per folder, largest last, so you know what to copy and how long
it may take.

### Step 3. Copy a folder with scp

**Runs on:** Local

This copies `/workspace/results` into the current folder on your computer:

```bash
scp -r root@spark-abcd.gpuwerk.com:/workspace/results ./
```

For many small files, pack them into one stream first, which is faster over the network:

```bash
ssh root@spark-abcd.gpuwerk.com 'tar -C /workspace -czf - results' > results.tar.gz
```

**Expected result:** a `results` folder, or `results.tar.gz`, in your current directory.

### Step 4. Sync large or changing folders with rsync

**Runs on:** Instance, then Local

`rsync` copies only what changed and can resume after a dropped connection, so it suits
checkpoints and long runs. It must be installed on both ends. On the instance:

```bash
apt-get update && apt-get install -y rsync
```

Then on your computer:

```bash
rsync -avz --partial --progress \
  root@spark-abcd.gpuwerk.com:/workspace/checkpoints/ ./checkpoints/
```

Leave out `-z` for files that are already compressed, such as `.safetensors` or `.gguf`.

**Expected result:** a progress line per file. Run the same command again later and it
fetches only new or changed files.

### Step 5. Push models and datasets to Hugging Face

**Runs on:** Instance

For a fine-tuned model or a large dataset, uploading straight from the instance to a private
Hugging Face repository is usually faster than downloading to a laptop.

```bash
pip install -U huggingface_hub
hf auth login                      # paste a token with write access
hf upload your-name/my-finetune /workspace/out . --private
```

For a dataset, add `--repo-type dataset`.

**Expected result:** the upload finishes with the URL of the repository, and the files are
listed there.

The token is stored under `~/.cache/huggingface` on the instance. Run `hf auth logout`
before you terminate, or use a token you revoke afterwards.

### Step 6. Check, then terminate

**Runs on:** Instance, Local, then the console

Compare sizes on both ends:

```bash
# Instance
du -sh /workspace/results
# Local
du -sh ./results
```

Write down or copy anything outside `/workspace` you will need to set up again. Then
terminate from the console. It asks you to type the instance name because it cannot be
undone.

**Expected result:** matching sizes, then the instance disappears from your list and billing
ends.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Permission denied (publickey)` | No key on the instance, or your agent has none | See [Connect to your instance](../connect-to-your-instance/), or use the Hugging Face route from the browser terminal |
| `rsync: command not found` | `rsync` is missing on one end | Install it on the instance with apt, and on your computer with your package manager |
| Transfer stops partway | The connection dropped | Run the same `rsync` command again; `--partial` resumes |
| `hf upload` fails with 401 or 403 | The token is read-only or for another account | Create a token with write access and run `hf auth login` again |
| Copy is smaller than the original | Transfer interrupted, or a path was missed | Rerun `rsync`, then compare `du -sh` again before terminating |

## Clean up

- Run `hf auth logout` on the instance, or revoke the token in Hugging Face.
- Terminate the instance in the console when the copy is complete; billing ends and the
  workspace is deleted.

## Further reading

- [Get your files out of a rented Spark](https://gpuwerk.com/docs/get-your-files-out/)
- [The tenant environment: what persists](https://gpuwerk.com/docs/tenant-environment/)
- [Hugging Face CLI guide](https://huggingface.co/docs/huggingface_hub/guides/cli)
- [rsync manual](https://download.samba.org/pub/rsync/rsync.1)
- Related playbooks: [Connect to your instance](../connect-to-your-instance/),
  [Keep services running](../keep-services-running/)
