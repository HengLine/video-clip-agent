# NeoClip Skills

本目录包含 NeoClip 视频混剪智能体项目的全套技能文件。

## 技能清单

| 技能文件             | 技能名称         | 用途                                 |
| :------------------- | :--------------- | :----------------------------------- |
| `project.md`         | 项目知识         | 架构、代码结构、V0.1 范围、版本路线  |
| `code-standards.md`  | 代码规范         | 类型注解、Pydantic、命名、导入、日志  |
| `validation.md`      | 代码校验         | pre-commit、ruff、black、mypy、pytest |
| `agent-development.md` | 智能体开发    | 工具创建、能力注册、AI 客户端、FFmpeg |

## 使用方式

在对话中描述你的意图，AI 助手会自动加载相关技能。例如：

- "我要创建一个新的视频分析工具" → 加载 `agent-development.md` + `code-standards.md`
- "这段代码格式不对，帮我修一下" → 加载 `code-standards.md` + `validation.md`
- "这个项目是怎么设计的？" → 加载 `project.md`
- "帮我审查一下这个 MR" → 加载全部技能

## 当前版本

**V0.1 — 星型骨架（MVP）**

核心能力：
- 视频上传 + 场景分割 + 语义标注 + 关键词匹配 + 片段拼接
- FastAPI REST API + 多 AI provider 支持
- 硬编码关键词指令解析
- 结构化日志 + 基础可观测性
