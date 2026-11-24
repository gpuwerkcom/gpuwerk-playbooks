# GPUwerk Playbooks

Step-by-step playbooks for running AI workloads on a dedicated NVIDIA DGX Spark rented from
[GPUwerk](https://gpuwerk.com): connecting, serving models, building tools on top of them, and
getting your work back out before you terminate.

Each playbook has an overview (what you end up with, prerequisites, time and risk), numbered
steps that say where each command runs and what you should see, a troubleshooting table and
clean-up steps. They are written against a GPUwerk instance: a container on a whole DGX Spark
(GB10, ARM64, 128 GB unified memory) where you are root and `/workspace` persists.

## Before you start

1. Create an account and deploy an instance in the [console](https://console.gpuwerk.com/deploy).
2. Read [The tenant environment](https://gpuwerk.com/docs/tenant-environment/) once. It explains
   what survives a restart, how networking works, and why some machines run Docker and others
   do not.
3. Running time is billed per minute. See [pricing](https://gpuwerk.com/pricing/) for current
   rates, and terminate the instance when you are done.

## Available playbooks

### Getting started

- [Connect to Your GPUwerk Instance](playbooks/connect-to-your-instance/)
- [Run Your First Model Evaluation](playbooks/first-model-evaluation/)
- [Keep Services Running Across Restarts](playbooks/keep-services-running/)
- [Copy Your Files Off Before You Terminate](playbooks/get-your-files-out/)

### Serving models

- [Serve Models with llama.cpp](playbooks/llama-cpp/)
- [Serve Models with vLLM](playbooks/vllm/)
- [Call Open Models with the Inference API](playbooks/inference-api/)

### Building on a model

- [Set Up Open WebUI as a Private Chat](playbooks/open-webui/)
- [Point a Coding Agent at Your Spark](playbooks/coding-agents/)

## Related

- [GPUwerk docs](https://gpuwerk.com/docs/): reference pages these playbooks build on
- [API reference](https://gpuwerk.com/docs/api-reference/)
- [Terraform provider](https://github.com/gpuwerkcom/terraform-provider-gpuwerk)
- [NVIDIA DGX Spark playbooks](https://github.com/NVIDIA/dgx-spark-playbooks): NVIDIA's own
  guides for a Spark on your desk. Most of them also work on a GPUwerk instance; the
  differences are covered in the tenant environment page.

## Contributing

Found a step that no longer works? Open an issue with the playbook name, the step and the
output you got. Pull requests are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache License 2.0, see [LICENSE](LICENSE). Third-party software installed by these playbooks
is under its own license.

GPUwerk is operated by PRINT IT! SE, Prague. NVIDIA and DGX Spark are trademarks of NVIDIA
Corporation. This repository is not affiliated with or endorsed by NVIDIA.
