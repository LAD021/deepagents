"""Daytona sandbox backend implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from deepagents.backends.protocol import ExecuteResponse
from deepagents_cli.config import detect_invoking_shell
import shlex
from deepagents.backends.sandbox import BaseSandbox

if TYPE_CHECKING:
    from daytona import Sandbox


class DaytonaBackend(BaseSandbox):
    """Daytona backend implementation conforming to SandboxBackendProtocol.

    This implementation inherits all file operation methods from BaseSandbox
    and only implements the execute() method using Daytona's API.
    """

    def __init__(self, sandbox: Sandbox) -> None:
        """Initialize the DaytonaBackend with a Daytona sandbox client.

        Args:
            sandbox: Daytona sandbox instance
        """
        self._sandbox = sandbox
        self._timeout: int = 30 * 60  # 30 mins

    @property
    def id(self) -> str:
        """Unique identifier for the sandbox backend."""
        return self._sandbox.id

    def execute(
        self,
        command: str,
    ) -> ExecuteResponse:
        """Execute a command in the sandbox and return ExecuteResponse.

        Args:
            command: Full shell command string to execute.

        Returns:
            ExecuteResponse with combined output, exit code, optional signal, and truncation flag.
        """
        shell_exe = detect_invoking_shell()
        wrapped = f"{shell_exe} -c {shlex.quote(command)}"
        result = self._sandbox.process.exec(wrapped, timeout=self._timeout)

        return ExecuteResponse(
            output=result.result,  # Daytona combines stdout/stderr
            exit_code=result.exit_code,
            truncated=False,
        )
