"""测试工作记忆日志中间件。"""

import os
from pathlib import Path

from deepagents_cli.working_memory_logger import WorkingMemoryLoggingMiddleware
from deepagents_cli.config import Settings


def test_working_memory_logger_writes_snapshot(tmp_path):
    """开启日志后应写入用户/项目记忆快照。"""
    os.environ["DEEPAGENTS_LOG_WORK_MEMORY"] = "true"
    os.environ["DEEPAGENTS_LOG_DIR"] = str(tmp_path)

    settings = Settings.from_environment(start_path=tmp_path)
    m = WorkingMemoryLoggingMiddleware(settings=settings, assistant_id="agent")

    state = {"user_memory": "UM", "project_memory": "PM"}
    m.before_agent(state, runtime=None)

    files = list(Path(tmp_path).glob("*.log"))
    assert files, "日志文件未生成"
    content = files[0].read_text(encoding="utf-8")
    assert "memory_snapshot" in content
    assert "UM" in content
    assert "PM" in content