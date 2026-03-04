# SPDX-FileCopyrightText: GitHub, Inc.
# SPDX-License-Identifier: MIT

import atexit
import logging
import os
import subprocess
import uuid
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field
from seclab_taskflow_agent.path_utils import log_file_name

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename=log_file_name("container_shell.log"),
    filemode="a",
)

mcp = FastMCP("ContainerShell")

_container_name: str | None = None

CONTAINER_IMAGE = os.environ.get("CONTAINER_IMAGE", "")
CONTAINER_WORKSPACE = os.environ.get("CONTAINER_WORKSPACE", "")
CONTAINER_TIMEOUT = int(os.environ.get("CONTAINER_TIMEOUT", "30"))

_DEFAULT_WORKDIR = "/workspace"


def _start_container() -> str:
    """Start the Docker container and return its name."""
    if not CONTAINER_IMAGE:
        raise RuntimeError("CONTAINER_IMAGE is not set — cannot start container")
    if CONTAINER_WORKSPACE and ":" in CONTAINER_WORKSPACE:
        raise RuntimeError(f"CONTAINER_WORKSPACE must not contain a colon: {CONTAINER_WORKSPACE!r}")
    name = f"seclab-shell-{uuid.uuid4().hex[:8]}"
    cmd = ["docker", "run", "-d", "--rm", "--name", name]
    if CONTAINER_WORKSPACE:
        cmd += ["-v", f"{CONTAINER_WORKSPACE}:/workspace"]
    cmd += [CONTAINER_IMAGE, "tail", "-f", "/dev/null"]
    logging.debug(f"Starting container: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"docker run failed: {result.stderr.strip()}")
    logging.debug(f"Container started: {name}")
    return name


def _stop_container() -> None:
    """Stop the running container."""
    global _container_name
    if _container_name is None:
        return
    logging.debug(f"Stopping container: {_container_name}")
    result = subprocess.run(
        ["docker", "stop", "--time", "5", _container_name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logging.warning(
            "docker stop failed for container %s: %s",
            _container_name,
            result.stderr.strip(),
        )
    _container_name = None


atexit.register(_stop_container)


@mcp.tool()
def shell_exec(
    command: Annotated[str, Field(description="Shell command to execute inside the container")],
    timeout: Annotated[int, Field(description="Timeout in seconds")] = CONTAINER_TIMEOUT,
    workdir: Annotated[str, Field(description="Working directory inside the container")] = _DEFAULT_WORKDIR,
) -> str:
    """Execute a shell command inside the managed Docker container."""
    global _container_name
    if _container_name is None:
        try:
            _container_name = _start_container()
        except RuntimeError as e:
            return f"Failed to start container: {e}"

    cmd = ["docker", "exec", "-w", workdir, _container_name, "bash", "-c", command]
    logging.debug(f"Executing: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return f"[exit code: timeout after {timeout}s]"

    output = result.stdout
    if result.stderr:
        output += result.stderr
    output += f"[exit code: {result.returncode}]"
    return output


if __name__ == "__main__":
    mcp.run(show_banner=False)
