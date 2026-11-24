# Connect to Your GPUwerk Instance

> Get a shell on a rented DGX Spark from your own computer, and reach its web UIs safely.

## Table of Contents

- [Overview](#overview)
- [Instructions](#instructions)
- [Troubleshooting](#troubleshooting)
- [Clean up](#clean-up)

---

## Overview

### Basic idea

Every GPUwerk instance has a browser terminal in the console, so you can work without any
setup. For your own terminal, `scp`, port forwarding or VS Code Remote-SSH, you add an SSH
key. This playbook creates the key, gives it to your instance, shortens the connection to
`ssh spark`, and forwards a port so a web UI on the instance opens in your local browser
without being exposed to the internet.

### What you'll accomplish

- An ed25519 SSH key loaded in your SSH agent.
- `ssh spark` opening a root shell on your instance.
- A tunnel that makes a port on the instance available as `http://localhost:<port>`.

### What to know before starting

- Basic terminal use on macOS, Linux or Windows PowerShell.

### Prerequisites

- A GPUwerk account. A running instance is needed from Step 4 onwards
  ([deploy one](https://console.gpuwerk.com/deploy)).
- OpenSSH on your computer (built into macOS, Linux and Windows 10/11).

### Where each step runs

| Label | Meaning |
|---|---|
| **Instance** | In the browser terminal or an SSH session on your GPUwerk instance |
| **Local** | On your own computer |

### Time and risk

- **Duration:** about 5 minutes.
- **Risk level:** Low. Nothing on the instance changes except its authorized keys.
- **Rollback:** delete the key from your account in the console; use **Reset SSH access**
  on the instance if you need to replace it.
- **Cost:** none beyond the instance's running time.
- **Last updated:** November 24, 2026, first publication.

## Instructions

### Step 1. Generate a key

**Runs on:** Local

If `ls ~/.ssh/*.pub` already lists `id_ed25519.pub` or `id_rsa.pub`, reuse that key and skip
to Step 2. Otherwise create one and set a passphrase when asked.

```bash
ssh-keygen -t ed25519 -C "you@example.com"
```

**Expected result:** `~/.ssh/id_ed25519` (private, never share it) and
`~/.ssh/id_ed25519.pub` (public), plus a `SHA256:` fingerprint in the terminal.

### Step 2. Load the key into the agent

**Runs on:** Local

The agent keeps the unlocked key in memory, so you type the passphrase once per session.

```bash
# macOS: also stores the passphrase in the keychain
ssh-add --apple-use-keychain ~/.ssh/id_ed25519

# Linux
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

```powershell
# Windows PowerShell, once as Administrator
Set-Service ssh-agent -StartupType Automatic
Start-Service ssh-agent
ssh-add $env:USERPROFILE\.ssh\id_ed25519
```

**Expected result:** `ssh-add -l` lists your key.

### Step 3. Give the public key to GPUwerk

**Runs on:** Local, then the console

Copy the whole public key line, from `ssh-ed25519` to the comment at the end:

```bash
# macOS
pbcopy < ~/.ssh/id_ed25519.pub
# Linux
cat ~/.ssh/id_ed25519.pub
```

- **New instance:** paste it into the SSH key field when you deploy. A key saved on your
  account earlier is used automatically.
- **Running instance without a key:** open it in the console and use **Reset SSH access**,
  or call `POST /v1/instances/<id>/reset-access` with `{"ssh_public_key": "..."}`.

Paste the `.pub` file only. If the text starts with `-----BEGIN OPENSSH PRIVATE KEY-----`, it
is the private key: stop and copy the other file.

**Expected result:** the instance page shows an SSH command.

### Step 4. Connect

**Runs on:** Local

Each instance has the hostname `<instance-name>.gpuwerk.com` and its own public IPv4. Connect
by hostname, because the address can change when an instance starts again.

```bash
ssh root@my-instance.gpuwerk.com
```

**Expected result:** a one-time host key prompt (type `yes`), then a root prompt. Keep your
files under `/workspace`: it is the part of the instance that survives a rebuild.

### Step 5. Shorten it to `ssh spark`

**Runs on:** Local

Add this block to `~/.ssh/config`, with your own hostname:

```text
Host spark
    HostName my-instance.gpuwerk.com
    User root
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
```

**Expected result:** `ssh spark` connects, `scp file.jsonl spark:/workspace/` copies a file,
and VS Code or Cursor Remote-SSH lists `spark` as a host.

### Step 6. Forward a web UI over SSH

**Runs on:** Local

A service bound to `0.0.0.0` on the instance can be reachable on its public address. For
anything private, bind it to `127.0.0.1` on the instance and forward the port:

```bash
# -N: tunnel only, no shell
ssh -N -L 8080:127.0.0.1:8080 spark
```

**Expected result:** while the command runs, `http://localhost:8080` in your browser is port
8080 on the instance. Add more `-L` flags for more ports.

Model presets also publish an HTTPS endpoint that needs an API key with the `inference`
scope. For confidential data, use the tunnel to port 8888 instead
(`ssh -N -L 8888:127.0.0.1:8888 spark`), which is encrypted end to end.

## Troubleshooting

The browser terminal in the console does not depend on your key, so you can always get a
shell there while you fix SSH.

| Symptom | Cause | Fix |
|---|---|---|
| `Permission denied (publickey)` | The instance has a different key, or your agent has none | `ssh -v spark` and read the `Offering public key` lines. Not offered: `ssh-add`. Offered and refused: **Reset SSH access** with the key you hold |
| `UNPROTECTED PRIVATE KEY FILE` | Others can read your private key | `chmod 700 ~/.ssh && chmod 600 ~/.ssh/id_ed25519` |
| `REMOTE HOST IDENTIFICATION HAS CHANGED` | A new instance reused the hostname | Only if you replaced the instance: `ssh-keygen -R my-instance.gpuwerk.com`. On an instance you did not change, treat the warning as an interception and stop |
| Locked out after editing `authorized_keys` or `sshd_config` | The key or SSH config on the instance is broken | Console: **Locked out? Reset SSH access**. It reinstalls your account's keys and the default `sshd_config`; `/workspace` and running processes are untouched |

## Clean up

- Stop the tunnel with Ctrl+C.
- Keys stay on your account for the next instance. Remove a key in the console if you no
  longer use it.

## Further reading

- [Create an SSH key and connect](https://gpuwerk.com/docs/ssh-keys/)
- [Use the in-browser terminal](https://gpuwerk.com/docs/browser-terminal/)
- [The tenant environment](https://gpuwerk.com/docs/tenant-environment/)
