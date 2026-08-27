# PenClip — 视频混剪智能体

基于**星型中枢分发架构**的 AI 视频混剪系统：自然语言驱动视频分析、片段匹配与自动合成。核心理念「人机协同」—— AI 辅助而非替代创作者。

## 当前状态
- 版本：**V0.1（DDD 分层骨架）**，开发分支 `dev`
- 顶层架构：星型中枢分发（`CentralHub`）+ 线性链路工作流（首个注册能力）
- 意图识别：V0.1 关键词匹配（`IntentRecognizer`），V0.2 才升级 LLM 语义理解
- 图编排：`LangGraphEngine` V0.1 仅 stub，V0.2 真正接入 LangGraph

## 分层架构（依赖方向：外层 → 内层，内层禁止反向依赖）
```
domain/          领域层：实体(Pydantic) + 值对象(dataclass/enum) + 仓储接口 —— 零依赖
core/            应用层：hub 分发 / orchestration / state / event —— 依赖 domain
agents/          智能体：BaseAgent + Planner/Analyzer/Matcher/Composer —— 依赖 domain+core
services/        服务层：llm/clip/ffmpeg/scene_detect/vector/file —— 多为 V0.2 stub
infrastructure/  基础设施：postgres/minio/redis/cache/messaging —— 实现仓储接口，多为 stub
api/             接入层：v1 REST / middleware / websocket / schemas
cli/             CLI 入口
plugins/         插件系统 + Docker 沙箱（V2.0）
```
遗留层（仍在使用，逐步迁移）：`client/`（多 AI 提供商）、`tools/`（6 个视频分析工具）、`utils/`（ffmpeg/redis/path/log 等）、`config/config.py`、`logger.py`

## Bridge 层（向后兼容转发，勿在此改逻辑）
顶层 `hub/`、`graph/`、`state/` 是兼容转发模块，真实实现在 `core/`、`domain/`：
- `penclip.hub.hub_core` → `penclip.core.hub.central_hub`（`get_hub`/`CentralHub`/`HubRequest`/`HubResponse`）
- `penclip.graph.hub_graph` → `penclip.core.orchestration.graph_engine`（`get_graph`/`LangGraphEngine`）
- `penclip.state.models` → `IntentType`(domain) + `TaskLifecycleStage`(core.state)

## 关键入口
```python
from penclip.hub.hub_core import get_hub           # 中枢单例
from penclip.graph.hub_graph import get_graph       # 图引擎（stub）
from penclip.state.models import IntentType, TaskLifecycleStage
from penclip.domain.value_objects.intent import IntentType  # 真实定义处
```
启动：`python main.py`（→ `penclip.app:app` FastAPI，默认 http://localhost:8000，`/docs` 交互文档）

## 核心契约（开发必读）
- `IntentType`（str Enum）：30+ 意图，6 类 —— 规划/分析/素材/效果/状态/通用
- `CapabilityDeclaration`（dataclass）：`name` + `intents` + `input_schema`/`output_schema` + `risk_level` + `version`
- `BaseAgent`（ABC）：`declare_capabilities()` + `execute(params, context)`，经 `CentralHub.register_agent()` 接入
- `ExecutionResult`（dataclass）：`success`/`data`/`message`/`suggestions`/`status`
- `AssemblyState`（Pydantic）：全局会话状态（assets/slots/analysis_results/match_results/global_context/...）

## 开发约定
- 所有 import 统一 `penclip.*` 前缀；**禁止** `penshot.*`/`neopen.*` 旧前缀
- 值对象用 `dataclass`+`enum`；实体与 API 模型用 Pydantic `BaseModel`
- 工具函数返回 `Dict` 带 `success` 字段、不抛异常；API 层用 `HTTPException`
- 用 `penclip.logger` 的 `debug/info/warning/error`，禁止 `print()`
- 每个工具/Agent 必须有 `DEFAULT_CONFIG`；能力注册是核心扩展机制，新增能力不修改中枢代码

## 详细文档
- 项目知识：`.claude/skills/project.md`（架构/目录/领域模型/V0.1 状态）
- 智能体开发：`.claude/skills/agent-development.md`
- 代码规范：`.claude/skills/code-standards.md`
- 代码校验：`.claude/skills/validation.md`
- 设计文档：`docs/视频混剪智能体-项目总结.md`（四文档精简，**先读**）、`docs/视频混剪智能体-设计原则.md`（目标架构）、`docs/视频混剪智能体-技术架构.md`、`docs/视频混剪智能体-版本演进.md`、`docs/AI开发导向-项目总览.md`