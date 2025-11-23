import types

import deepagents_cli.commands as commands_mod


def test_execute_bash_command_uses_detected_shell(monkeypatch):
    calls = {}

    def fake_run(cmd, **kwargs):
        calls["cmd"] = cmd
        calls["kwargs"] = kwargs
        return types.SimpleNamespace(stdout="", stderr="", returncode=0)

    monkeypatch.setattr(commands_mod, "detect_invoking_shell", lambda: "/bin/zsh")
    monkeypatch.setattr(commands_mod.subprocess, "run", fake_run)

    assert commands_mod.execute_bash_command("!echo hi") is True
    assert calls["kwargs"]["executable"] == "/bin/zsh"
    assert calls["kwargs"]["shell"] is True