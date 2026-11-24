# Keep Services Running Across Restarts

> Start your own services so they survive a dropped SSH session and come back after every restart.

## Table of Contents

- [Overview](#overview)
- [Instructions](#instructions)
- [Troubleshooting](#troubleshooting)
- [Clean up](#clean-up)

---

## Overview

### Basic idea

A GPUwerk instance is your own container on a dedicated DGX Spark, not a full Linux host. A
process started in a plain SSH session dies when the session ends, and nothing outside
`/workspace` is guaranteed to come back after a rebuild. This playbook uses `tmux` for work
that must outlive a disconnect, the startup hook `/workspace/.gpuwerk-init` for services that
must start on every container start, and a systemd unit on machines that run systemd.

### What you'll accomplish

- A long-running command inside `tmux` that keeps going after you disconnect.
- A startup hook that starts your services after every restart or rebuild, with its output
  in `/workspace/.gpuwerk-init.log`.
- Optionally, a systemd unit, on instances where systemd is PID 1.
- Services bound to `127.0.0.1` unless you mean them to be public.

### What to know before starting

- Basic terminal use and shell scripts.
- Knowing which command starts your service, and which port it listens on.

### Prerequisites

- A GPUwerk account with credit, and a running instance on DGX OS 7 or Ubuntu 24.04
  ([console](https://console.gpuwerk.com/deploy)).
- A shell on the instance: the console's browser terminal, or SSH
  ([Connect to your instance](../connect-to-your-instance/)).

### Where each step runs

| Label | Meaning |
|---|---|
| **Instance** | In the browser terminal or an SSH session on your GPUwerk instance |
| **Local** | On your own computer |

### Time and risk

- **Duration:** about 10 minutes, plus one instance restart.
- **Risk level:** Low. The hook runs detached, so a broken script cannot block SSH.
- **Rollback:** delete `/workspace/.gpuwerk-init` (and any unit you added) and restart.
- **Cost:** running time is billed per minute at the rate shown in the console;
  see [pricing](https://gpuwerk.com/pricing/).
- **Last updated:** November 24, 2026, first publication.

## Instructions

### Step 1. Know what survives

**Runs on:** Instance

`/workspace` is a separate volume, not part of the container's own filesystem.

| Action | Under `/workspace` | Everything else (apt packages, system pip installs) |
|---|---|---|
| Restart | Kept | Kept |
| Stop and start | Kept | Kept while the machine is held |
| Rebuild | Kept | Gone: the image is reinstalled fresh |
| Terminate | Deleted for good | Deleted |

Keep scripts, models, virtual environments and logs under `/workspace`. If a service depends
on something you installed with `apt`, reinstall it from the startup hook, or it will be
missing after a rebuild. We keep no backup of `/workspace`; see
[Get your files out](../get-your-files-out/).

```bash
ls -la /workspace
```

**Expected result:** your files, plus `.hostkeys` (the instance's SSH host keys, kept here so
its identity stays the same across restarts).

### Step 2. Check whether you have systemd and Docker

**Runs on:** Instance

Some machines run a system container (systemd is PID 1, Docker is installed) and the rest
run a plain container (no systemd, no Docker daemon). You cannot pick which one you get
when you deploy, so check:

```bash
docker info
```

**Expected result:** on a system container, Docker prints its server details and Step 5 is
available to you. On a plain container the command fails; use Steps 3 and 4 only.

### Step 3. Use tmux for work that must survive a disconnect

**Runs on:** Instance

A process started inside `tmux` keeps running when your SSH session or browser tab closes.
Install it if `tmux` is not found:

```bash
apt-get update && apt-get install -y tmux
tmux new -s work
```

Start your command in the session, then detach with Ctrl+B, then D. Later, reattach:

```bash
tmux attach -t work
```

**Expected result:** after you reconnect, `tmux ls` lists `work` and your command is still
running. `tmux` does not survive a restart of the instance; for that, use Step 4.

### Step 4. Add the startup hook

**Runs on:** Instance

`/workspace/.gpuwerk-init` runs as root on every container start: first boot, restart and
rebuild. It is launched detached, and its output goes to `/workspace/.gpuwerk-init.log`, not
your terminal. Start each service in the background so the script finishes quickly.

```bash
cat > /workspace/.gpuwerk-init <<'EOF'
#!/bin/sh
# /workspace/.gpuwerk-init: must not block, it runs detached anyway
cd /workspace
nohup llama-server -m my-model.gguf --host 127.0.0.1 --port 8899 \
    >> llama-server.log 2>&1 &
nohup python3 my-service.py >> my-service.log 2>&1 &
EOF
chmod +x /workspace/.gpuwerk-init
```

Replace the two `nohup` lines with your own commands. Use full paths for anything installed
under `/workspace`, such as a virtual environment's `python`. Then restart the instance from
the console.

The hook needs an image built after September 19, 2026. If your instance is older, a rebuild
picks up the new image and keeps `/workspace`.

**Expected result:** after the restart, `/workspace/.gpuwerk-init.log` has a new timestamp
line followed by your script's output, and `ps aux` shows your services. Each run writes its
own timestamp line, so you can tell restarts apart:

```bash
tail -n 20 /workspace/.gpuwerk-init.log
```

### Step 5. Optional: use a systemd unit on a system container

**Runs on:** Instance

Only if `docker info` answered in Step 2. A unit gives you restarts on failure and
`journalctl` logs. Keep the program and its data under `/workspace`.

```bash
cat > /etc/systemd/system/my-service.service <<'EOF'
[Unit]
Description=My service
After=network-online.target

[Service]
WorkingDirectory=/workspace
ExecStart=/usr/bin/python3 /workspace/my-service.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now my-service
```

**Expected result:** `systemctl status my-service` shows `active (running)`, and
`journalctl -u my-service` shows its output.

Units in `/etc/systemd` are outside `/workspace`, so a rebuild removes them. Keep a copy of
the unit file under `/workspace` and have the startup hook copy it back and enable it, or
recreate it after a rebuild. On a system container, Docker keeps its images and containers
in `/workspace/docker`, so they survive a rebuild and use workspace space.

### Step 6. Choose who can reach each service

**Runs on:** Instance, then Local

Each instance has its own public IPv4. A service bound to `0.0.0.0` listens on the
instance's network interface and can be reachable from the internet. A service bound to
`127.0.0.1` is reachable only from inside the instance.

```bash
ss -tlnp
```

For anything private, bind to `127.0.0.1` and open it from your computer through an SSH
tunnel ([Connect to your instance](../connect-to-your-instance/), Step 6):

```bash
# Local
ssh -N -L 8899:127.0.0.1:8899 spark
```

If you do bind to `0.0.0.0`, put authentication in front of the service, for example an API
key on the model server.

**Expected result:** `ss -tlnp` shows each service on the address you chose, and
`http://localhost:8899` on your computer reaches the private one while the tunnel runs.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Process gone after closing the terminal | It was started in the session, not in `tmux` or the hook | Start it inside `tmux` (Step 3) or from the startup hook (Step 4) |
| No new line in `/workspace/.gpuwerk-init.log` after a restart | The file is not executable, or the image predates hook support | `chmod +x /workspace/.gpuwerk-init`; on an older instance, rebuild |
| Log shows `not found` for your command | It was installed with apt or system pip and a rebuild removed it, or `PATH` differs | Use full paths, keep tools under `/workspace`, or reinstall them in the hook |
| `systemctl` fails with "System has not been booted with systemd" | Plain container: PID 1 is not systemd | Use the startup hook instead |
| `docker run` cannot connect to the Docker daemon | Plain container: no Docker daemon or socket | Install tools with pip or apt and use the startup hook |
| Service reachable from the internet | It is bound to `0.0.0.0` | Bind to `127.0.0.1` and use an SSH tunnel, or add authentication |

## Clean up

- Remove the hook with `rm /workspace/.gpuwerk-init`, and on a system container
  `systemctl disable --now my-service`.
- Copy anything you want to keep off `/workspace` first
  ([Get your files out](../get-your-files-out/)).
- Terminate the instance in the console when you are done; billing ends and the
  workspace is deleted.

## Further reading

- [The tenant environment](https://gpuwerk.com/docs/tenant-environment/)
- [Create an SSH key and connect](https://gpuwerk.com/docs/ssh-keys/)
- [tmux wiki: Getting Started](https://github.com/tmux/tmux/wiki/Getting-Started)
- [systemd.service manual](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)
- Related playbooks: [Serve models with llama.cpp](../llama-cpp/), [Serve models with vLLM](../vllm/)
