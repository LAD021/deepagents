## 目标
- 将会话运行时“工作记忆”（系统提示、用户/项目记忆片段、模型请求与响应摘要）落盘到 `log/` 文件夹，默认每会话一个日志文件，便于审计与回溯。

## 现状与位置
- 运行时工作记忆为进程内存，不持久化：`InMemorySaver` 设置在 `deepagents_cli/agent.py:389`。
- 长期记忆来源：
  - 用户级：`~/.deepagents/{assistant_id}/agent.md`（加载位置 `deepagents_cli/agent_memory.py:230-237`）
  - 项目级：`[project-root]/.deepagents/agent.md` 或 `[project-root]/agent.md`（加载位置 `deepagents_cli/agent_memory.py:240-247`，路径解析 `deepagents_cli/config.py:200-211`）
- 系统提示构建与注入：`deepagents_cli/agent_memory.py:250-297`。

## 设计方案
- 目录解析：
  - 若处于项目内（`settings.project_root` 存在），日志目录为 `[project-root]/log`；否则为 `~/.deepagents/{assistant_id}/log`。
  - 支持显式覆盖：`DEEPAGENTS_LOG_DIR` 环境变量。
- 开关与配置（环境变量）：
  - `DEEPAGENTS_LOG_WORK_MEMORY=true|false`（默认 false）
  - `DEEPAGENTS_LOG_DIR=/abs/path/to/log`
  - `DEEPAGENTS_LOG_MAX_SIZE=5MB`、`DEEPAGENTS_LOG_BACKUPS=3`（可选，简单轮转）
- 中间件实现：新增 `WorkingMemoryLoggingMiddleware`（独立于现有内存注入中间件），职责：
  1. 在 `before_agent` 读取到的 `user_memory` 与 `project_memory` 就绪后，生成/打开日志文件并写入“记忆快照”。
  2. 在 `wrap_model_call`/`awrap_model_call` 阶段，记录：
     - `assistant_id`、会话 `thread_id`（来源 `SessionState.thread_id`，`deepagents_cli/config.py:279`）
     - `system_prompt`（截断到例如 8KB）
     - 请求 `messages` 概要（角色与长度，不写具体敏感内容）
     - 响应摘要（`finish_reason`、token 使用、内容长度）
  3. 敏感信息屏蔽：对环境变量名包含 `KEY|TOKEN|SECRET` 的值、以及 `.env` 中的常见密钥字段进行 `****` 屏蔽；不写原始密钥。
  4. 文件命名：`{assistant_id}-{thread_id}-{timestamp}.log`，UTF-8，纯文本或 JSON 行模式（建议 JSONL 便于后续分析）。
- 中间件挂载：在 `deepagents_cli/agent.py:create_agent_with_config` 的 `agent_middleware` 列表尾部追加（本地与远程模式均适用）。

## 测试方案
- 单元测试：
  - 使用 `tmp_path` 设置 `DEEPAGENTS_LOG_DIR` 与 `DEEPAGENTS_LOG_WORK_MEMORY=true`，构造最小请求，断言日志文件生成且包含 `user_memory`/`project_memory` 字样与 `assistant_id`、`thread_id`。
  - 断言未开启开关时不产生日志。
  - 断言屏蔽逻辑：人工注入伪环境变量 `OPENAI_API_KEY=xxx`，日志中应为 `****`。
- 集成测试：在 `tests/integration_tests/benchmarks/test_simple_tasks.py` 的运行路径下启用开关，验证 `log` 目录生成与日志条目随工具调用产生。

## 兼容与风险
- 默认关闭，避免磁盘膨胀与泄露风险；只在显式开启时记录。
- 按会话轮转与截断，避免巨大系统提示写入导致性能问题。
- 不改变现有记忆加载与系统提示注入逻辑（零破坏）；仅新增旁路记录。

## 具体改动点
- 新增中间件文件：`deepagents_cli/working_memory_logger.py`（或合并到现有中间件目录）。
- 在 `deepagents_cli/agent.py:309-316/329-331` 的 `agent_middleware` 末尾追加该中间件（读取开关后才加）。
- 文档注释与函数级注释全部为 Unicode，说明日志格式与安全策略。
- 不引入额外三方库（先使用标准库 `json`/`logging`），保持简洁。

## 完成标准
- 在开启开关条件下，`log/` 中产生会话日志；单测覆盖上述场景并通过；现有单元测试不受影响。