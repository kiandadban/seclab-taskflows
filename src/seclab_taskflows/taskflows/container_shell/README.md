# Container Shell Taskflows

Runs arbitrary CLI commands inside an isolated Docker container. One container
per MCP server process — started on the first `shell_exec` call, stopped on
exit. An optional host directory is mounted at `/workspace` inside the container.

Three container profiles are provided. Each has its own Dockerfile, toolbox
YAML, and demo taskflow.

## Profiles

**base** (`seclab-shell-base:latest`)
General-purpose. Includes bash, coreutils, python3, file, binutils, xxd,
curl, wget, git.

**malware-analysis** (`seclab-shell-malware-analysis:latest`)
Static binary and firmware analysis. Extends base with radare2, binwalk,
yara, exiftool, checksec, capstone, pwntools, volatility3.

**network-analysis** (`seclab-shell-network-analysis:latest`)
Packet capture analysis and network recon. Extends base with nmap, tcpdump,
tshark, netcat, dig, jq, httpie.

## Building the images

Run from the repository root:

```
./scripts/build_container_images.sh
```

To build a single profile (the base image is always built first when needed):

```
./scripts/build_container_images.sh base
./scripts/build_container_images.sh malware
./scripts/build_container_images.sh network
```

Images only need to be rebuilt when a Dockerfile changes.

## Environment variables

`CONTAINER_WORKSPACE` — host path to mount at `/workspace`. Optional; omit if
you do not need to pass files into the container.

`CONTAINER_TIMEOUT` — default command timeout in seconds. Defaults to 30 (base
and network) or 60 (malware analysis).

`LOG_DIR` — where to write `container_shell.log`.

## Running the demos

Create a workspace directory with a target file, then run the agent:

**Base demo** — inspects any ELF binary using standard binutils:

```
cp /bin/ls /tmp/demo/hello
CONTAINER_WORKSPACE=/tmp/demo python -m seclab_taskflow_agent \
    -t seclab_taskflows.taskflows.container_shell.demo_base
```

**Malware analysis demo** — static triage of a suspicious ELF (not executed):

```
cp /bin/ls /tmp/samples/suspicious.elf
CONTAINER_WORKSPACE=/tmp/samples python -m seclab_taskflow_agent \
    -t seclab_taskflows.taskflows.container_shell.demo_malware_analysis
```

Override the target filename with `-g target=<name>`.

**Network analysis demo** — analyses a pcap file:

```
CONTAINER_WORKSPACE=/tmp/captures python -m seclab_taskflow_agent \
    -t seclab_taskflows.taskflows.container_shell.demo_network_analysis \
    -g capture=sample.pcap
```

## Using container_shell in your own taskflows

Reference the appropriate toolbox and set `CONTAINER_WORKSPACE` in `env`:

```yaml
taskflow:
  - task:
      agents:
        - seclab_taskflow_agent.personalities.assistant
      toolboxes:
        - seclab_taskflows.toolboxes.container_shell_malware_analysis
      env:
        CONTAINER_WORKSPACE: "{{ env('SAMPLE_DIR') }}"
      user_prompt: |
        Analyse the binary at /workspace/target.elf using static analysis only.
```

`shell_exec` requires user confirmation by default (`confirm: [shell_exec]` in
all toolbox YAMLs). Pass `headless: true` at the task level to skip
confirmation in automated pipelines.

## Notes

- The container is shared across all `shell_exec` calls within a single
  taskflow run. State (files written, processes started) persists between calls.
- `--rm` is set on `docker run`, so the container is removed automatically when
  stopped.
- The container name follows the pattern `seclab-shell-<8 hex chars>` and is
  visible in `docker ps`.
- If `docker run` fails (e.g. image not found), `shell_exec` returns an error
  string rather than raising, so the agent can report the problem cleanly.
