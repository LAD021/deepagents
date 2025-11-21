"""测试 .env 加载的备用路径与模型创建。

验证当当前工作目录无 .env 时，仍可从 DEEPAGENTS_ENV_PATH 指向的路径加载。"""

import os
import sys
from pathlib import Path


def test_env_fallback_loading(tmp_path):
    """设置 DEEPAGENTS_ENV_PATH 后应能加载密钥并创建 OpenAI 模型。"""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "OPENAI_API_KEY=dummy-key",
                "OPENAI_MODEL=gpt-5-mini",
            ]
        ),
        encoding="utf-8",
    )
    os.environ["DEEPAGENTS_ENV_PATH"] = str(env_file)

    sys.modules.pop("deepagents_cli.config", None)
    from deepagents_cli import config  # type: ignore

    model = config.create_model()
    assert model is not None