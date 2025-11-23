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


def test_mac_cmd_iverilog_version():
    """仅在macOS执行：运行 `iverilog -V`，检测到版本信息则通过，否则学习性 xfail。"""
    if sys.platform != "darwin":
        import pytest
        pytest.skip("仅在macOS运行该测试")

    with console.capture() as cap:
        assert execute_bash_command("iverilog -V") is True

    output = cap.get()
    import pytest
    if re.search(r"Icarus Verilog.*version\s+\d+(?:\.\d+)*", output, re.IGNORECASE):
        assert True
    else:
        pytest.xfail("iverilog未安装或不可用，学习性测试标记为xfail")