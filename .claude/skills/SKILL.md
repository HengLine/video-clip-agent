# PenClip Skills

本目录包含 PenClip 视频混剪智能体项目的全套技能文件。根目录 `CLAUDE.md` 是始终加载的项目入口，此处为按需加载的详细技能。

## 技能清单

| 技能文件             | 技能名称         | 用途                                 |
| :------------------- | :--------------- | :----------------------------------- |
| `project.md`         | 项目知识         | DDD 分层架构、目录结构、领域模型、中枢分发、V0.1 实现/Stub 状态、版本路线 |
| `code-standards.md`  | 代码规范         | 分层依赖、dataclass/Pydantic、类型注解、命名、导入、日志 |
| `validation.md`      | 代码校验         | pre-commit、ruff、black、mypy、pytest |
| `agent-development.md` | 智能体开发    | BaseAgent、能力注册、意图类型、AI 客户端、服务层、FFmpeg |

## 使用方式

在对话中描述你的意图，AI 助手会自动加载相关技能。例如：

- "我要创建一个新的 Agent 处理 XX 意图" → 加载 `agent-development.md` + `project.md`
- "这段代码格式不对，帮我修一下" → 加载 `code-standards.md` + `validation.md`
- "这个项目是怎么设计的？中枢怎么分发？" → 加载 `project.md`
- "帮我审查一下这个 MR" → 加载全部技能

## 当前版本

**V0.1 — DDD 分层骨架**

核心能力：
- 星型中枢分发（`CentralHub` + 能力注册）+ 线性链路工作流
- DDD 分层：domain（零依赖）/ core / agents / services / infrastructure / api
- 领域模型完整（Pydantic 实体 + dataclass 值对象 + 30+ 意图枚举）
- 关键词意图识别（V0.2 升级 LLM）；LangGraph 编排（V0.1 stub，V0.2 接入）
- 遗留层共存：`client/`（多 AI 提供商）、`tools/`（6 分析工具）、`utils/`