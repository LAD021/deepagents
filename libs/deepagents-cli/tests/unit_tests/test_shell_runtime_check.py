import os
import sys

from deepagents_cli.commands import execute_bash_command
from deepagents_cli.config import console


def test_runtime_shell_matches_current_os_shell():
    """使用与src同配置执行shell，检测当前测试所用OS壳与运行壳是否一致。"""
    if sys.platform != "darwin":
        import pytest
        pytest.skip("仅在macOS运行该测试")
    current_shell_path = "/bin/zsh"
    current_shell_name = os.path.basename(current_shell_path)

    with console.capture() as cap:
        assert execute_bash_command("!printf %s $0") is True
    output = cap.get()

    # 输出格式：第一行命令提示，随后是命令输出和可能的空行
    lines = [l for l in output.splitlines() if l.strip()]
    reported = lines[-1] if lines else ""
    if reported.startswith("-"):
        reported = reported[1:]
    reported_name = os.path.basename(reported)
    assert current_shell_name == reported_name

    # 可读性断言：是否zsh
    is_zsh = current_shell_name == "zsh"
    assert (reported_name == "zsh") == is_zsh