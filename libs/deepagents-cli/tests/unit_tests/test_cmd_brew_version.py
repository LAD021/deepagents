import sys
import re

from deepagents_cli.commands import execute_bash_command
from deepagents_cli.config import console


def test_mac_cmd_brew_version():
    """仅在macOS执行：运行 `brew --version` 并验证输出或缺失提示。"""
    if sys.platform != "darwin":
        import pytest
        pytest.skip("仅在macOS运行该测试")

    with console.capture() as cap:
        assert execute_bash_command("brew --version") is True

    output = cap.get()
    assert re.search(r"Homebrew\s+\d+\.\d+\.\d+", output) is not None, output