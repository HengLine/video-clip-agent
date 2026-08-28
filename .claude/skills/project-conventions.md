---
name: project-conventions
description: PenClip project-specific conventions for Python/FastAPI, video processing, multi-agent boundaries, and sensitive configuration. Use when implementing or reviewing project code.
type: reference
user-invocable: false
---

# PenClip 项目约定

## 适用范围

本文档补充 `CLAUDE.md`、`project.md`、`agent-development.md` 和 `code-standards.md`，只记录跨模块实现时最容易出错的约束。发生冲突时，以根目录 `CLAUDE.md` 为准。

## API 边界

- API 请求和响应使用 `api/schemas/` 中的 Pydantic 模型，不让领域实体直接承担 HTTP 契约。
- HTTP 状态码、认证、请求解析和异常转换留在 `api/` 层；Agent 和服务层不处理 FastAPI `Request` 或 `HTTPException`。
- 新路由优先放在 `api/v1/`，并通过现有路由装配注册。

## 视频处理

- 文件路径、输出目录和 FFmpeg 参数来自配置或调用参数，不硬编码到 Agent 中。
- FFmpeg、OpenCV、音频和场景分析操作放在 `services/` 或现有 `utils/` 适配层；Agent 只负责编排和结果契约。
- 外部命令执行必须使用现有安全封装，避免把用户输入直接拼接进 shell 命令。
- 长耗时处理返回结构化状态或任务标识，不在 API 请求处理中伪装成同步完成。

## 多 Agent 协作

- Agent 之间通过 `CentralHub`、领域值对象和 `ExecutionContext` 交换数据，不直接调用另一个 Agent 的私有实现。
- 新能力必须声明明确的 intent、输入输出 schema、风险等级和版本，并通过注册机制接入。
- 高风险操作保留 `RiskAssessor` 的确认流程，不在 Agent 内部绕过确认。

## 配置与密钥

- API Token、数据库密码和对象存储凭据只能来自外部环境变量或本地未跟踪配置。
- 不把 `.env`、`settings.local.json`、密钥和真实连接串加入提交；示例配置使用占位值。
- 修改配置加载逻辑时，同时确认项目启动入口、CLI 和测试环境的行为一致。

## 提交前

执行范围与命令以 `validation.md` 和 `pyproject.toml` 为准。至少根据变更范围检查格式、ruff、mypy 和相关 pytest；涉及 API、配置、Agent 或视频工具时优先运行对应测试。
