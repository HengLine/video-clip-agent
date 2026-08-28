# PenClip Skills

本目录保存按需阅读的项目参考文档。根目录 `CLAUDE.md` 负责最小项目上下文与硬性约定；本文档用于选择更详细的专题文档。

## 选择指南

| 技能文件             | 技能名称         | 用途                                 |
| :------------------- | :--------------- | :----------------------------------- |
| `project.md`         | 项目知识         | DDD 分层架构、目录结构、领域模型、中枢分发、V0.1 实现/Stub 状态、版本路线 |
| `code-standards.md`  | 代码规范         | 分层依赖、dataclass/Pydantic、类型注解、命名、导入、日志 |
| `validation.md`      | 代码校验         | pre-commit、ruff、black、mypy、pytest |
| `agent-development.md` | 智能体开发       | BaseAgent、能力注册、意图类型、LLM 客户端、服务层、工作流集成 |

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