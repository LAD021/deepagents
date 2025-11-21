"""工作记忆日志中间件。

该中间件负责将会话运行时的工作记忆（用户/项目记忆快照、系统提示与请求/响应摘要）
以 JSON Lines 形式追加写入日志文件，便于审计与回溯。
"""

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict

from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ModelRequest,
    ModelResponse,
)

from .config import Settings


class WorkingMemoryLoggingMiddleware(AgentMiddleware):
    """将工作记忆与调用摘要写入日志文件的中间件。"""

    state_schema = AgentState

    def __init__(self, *, settings: Settings, assistant_id: str) -> None:
        """初始化日志中间件。

        参数：
        - settings: 全局设置（含项目根路径等）
        - assistant_id: 代理标识，用于区分日志与用户内存目录
        """
        self.settings = settings
        self.assistant_id = assistant_id

        explicit_dir = os.environ.get("DEEPAGENTS_LOG_DIR")
        if explicit_dir:
            base_dir = Path(explicit_dir)
        elif self.settings.project_root:
            base_dir = Path(self.settings.project_root) / "log"
        else:
            base_dir = Path.home() / ".deepagents" / assistant_id / "log"

        base_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        self.session_id = str(uuid.uuid4())
        self.log_path = base_dir / f"{assistant_id}-{self.session_id}-{ts}.log"

        self.enabled = os.environ.get("DEEPAGENTS_LOG_WORK_MEMORY", "false").lower() in {
            "1",
            "true",
            "yes",
        }

    def _redact(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """简单敏感信息屏蔽：将 key/token/secret 字段值替换为 ****。"""
        redacted = {}
        for k, v in data.items():
            if any(s in k.lower() for s in ["key", "token", "secret"]):
                redacted[k] = "****"
            else:
                redacted[k] = v
        return redacted

    def _write(self, kind: str, payload: Dict[str, Any]) -> None:
        """写入一条 JSON 行日志。"""
        if not self.enabled:
            return
        entry = {
            "ts": int(time.time() * 1000),
            "kind": kind,
            "assistant_id": self.assistant_id,
            "session_id": self.session_id,
            "data": payload,
        }
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def before_agent(self, state: AgentState, runtime) -> Dict[str, Any]:
        """在代理执行前记录用户/项目记忆快照。"""
        try:
            user_mem = state.get("user_memory")
            proj_mem = state.get("project_memory")
            self._write(
                "memory_snapshot",
                {
                    "user_memory_present": bool(user_mem),
                    "project_memory_present": bool(proj_mem),
                    "user_memory_preview": (user_mem[:2048] if isinstance(user_mem, str) else None),
                    "project_memory_preview": (proj_mem[:2048] if isinstance(proj_mem, str) else None),
                },
            )
        except Exception:
            # 保持容错，不影响主流程
            pass
        return {}

    def wrap_model_call(self, request: ModelRequest, handler) -> ModelResponse:
        """记录系统提示与响应摘要。"""
        try:
            sys_prompt = request.system_prompt or ""
            self._write(
                "request",
                {
                    "system_prompt_preview": sys_prompt[:8192],
                },
            )
        except Exception:
            pass
        response = handler(request)
        try:
            summary = getattr(response, "response_metadata", None)
            usage = getattr(response, "usage_metadata", None)
            self._write(
                "response",
                {
                    "response_metadata": summary,
                    "usage_metadata": usage,
                },
            )
        except Exception:
            pass
        return response

    async def awrap_model_call(self, request: ModelRequest, handler) -> ModelResponse:
        """异步记录系统提示与响应摘要。"""
        try:
            sys_prompt = request.system_prompt or ""
            self._write(
                "request",
                {
                    "system_prompt_preview": sys_prompt[:8192],
                },
            )
        except Exception:
            pass
        response = await handler(request)
        try:
            summary = getattr(response, "response_metadata", None)
            usage = getattr(response, "usage_metadata", None)
            self._write(
                "response",
                {
                    "response_metadata": summary,
                    "usage_metadata": usage,
                },
            )
        except Exception:
            pass
        return response