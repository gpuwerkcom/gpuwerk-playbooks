# Contributing

Thank you for helping keep these playbooks correct.

## Reporting a problem

Open an issue with:

- the playbook and step number;
- the image or preset you deployed (DGX OS 7, Ubuntu 24.04, or a model preset);
- the command you ran and the full output.

Do not paste API keys, private SSH keys or Hugging Face tokens.

## Writing or changing a playbook

1. Copy [`playbooks/_template/`](playbooks/_template/) to `playbooks/<short-name>/`.
2. Keep the sections in the template's order: Overview, Instructions, Troubleshooting,
   Clean up, Further reading.
3. Label every step with where it runs (**Instance** or **Local**) and end it with an
   **Expected result**.
4. Test every command on a real GPUwerk instance before opening the pull request, and say in
   the pull request which image you tested on and when.
5. Keep files the reader should keep under `/workspace`; everything else is lost on a rebuild.
6. Prefer binding services to `127.0.0.1` and reaching them through an SSH tunnel. If a step
   binds to `0.0.0.0`, say that the port becomes reachable on the instance's public address
   and how to protect it.
7. Do not put prices in a playbook. Link to [pricing](https://gpuwerk.com/pricing/) instead.
8. Add the playbook to the list in the root [README](README.md) and update its
   **Last updated** line.

Run the link check before you push:

```bash
python3 scripts/check_links.py
```

By contributing you agree that your contribution is licensed under the Apache License 2.0.
