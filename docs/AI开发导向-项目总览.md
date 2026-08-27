# PenClip 项目总览 — AI 开发导向

> 生成时间: 2026-08-04 | 版本: V0.1 | 分支: dev
> 本文档为 AI 开发者视角编写，所有路径相对于项目根 `E:\Projects\neopen\video-clip-agent`

---

## 1. 项目身份

| 属性 | 值 |
|------|-----|
| 项目名称 | PenClip — 视频混剪智能体 |
| 包名 | `penclip` (PyPI: `penclip`) |
| 代码仓库 | `github.com/neopen/video-clip-agent` |
| 文档站点 | `clip.pengline.cn` |
| Python | >= 3.9 |
| Web 框架 | FastAPI + uvicorn |
| 架构模式 | 星型中枢分发 (Star-Hub Distribution) |
| 当前阶段 | V0.1 — 基础框架搭建，关键字命令解析 |

---

## 2. 架构概述

### 2.1 顶层架构：星型中枢分发

```
                         ┌─────────────────┐
                         │   CLI / HTTP     │
                         └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │   Central Hub   │  ← 命令解析 → 意图路由 → 能力调度
                         │  (待实现)        │
                         └───┬───┬───┬─────┘
                             │   │   │
                    ┌────────┘   │   └────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │ Agent A  │ │ Agent B  │ │ Agent C  │  ← 注册 intents + schemas
              └──────────┘ └──────────┘ └──────────┘
```

- **Hub** 负责命令解析、意图识别、能力路由（V0.2 起加入 LLM 语义理解）
- **Agents** 注册自己的意图 + 输入/输出 schema，Hub 按意图分发
- **当前注册的首个能力**: 线性链路节点模式 (Linear Pipeline Workflow)

### 2.2 三层命令处理模型

```
全局规划层 → Agent 导向层 → 属性修改层
(capability)   (agent+intent)   (property changes)
```

### 2.3 人机协同点

关键决策节点（素材选择、风格确认、输出预览）设置 **确认/取消** 检查点，用户可中断或调整。

---

## 3. 代码仓库结构

### 3.1 目录总览

```
video-clip-agent/
├── src/penclip/
│   ├── __init__.py
│   │
│   ├── core/                             # 核心模块
│   │   ├── __init__.py
│   │   ├── hub/                          # 中枢层
│   │   │   ├── __init__.py
│   │   │   ├── central_hub.py            # CentralHub - 指令解析中枢
│   │   │   ├── capability_registry.py    # CapabilityRegistry - 能力注册表
│   │   │   ├── intent_recognizer.py      # IntentRecognizer - 意图识别
│   │   │   ├── risk_assessor.py          # RiskAssessor - 风险评估
│   │   │   └── context_manager.py        # ContextManager - 上下文管理
│   │   │
│   │   ├── orchestration/                # 编排层
│   │   │   ├── __init__.py
│   │   │   ├── workflow_orchestrator.py  # WorkflowOrchestrator
│   │   │   ├── graph_engine.py           # LangGraphEngine
│   │   │   └── graph_factory.py          # GraphFactory - 图工厂
│   │   │
│   │   ├── state/                        # 状态管理
│   │   │   ├── __init__.py
│   │   │   ├── state_schema.py           # 状态数据模型
│   │   │   ├── state_manager.py          # StateManager
│   │   │   ├── state_store.py            # StateStore 接口
│   │   │   ├── memory_store.py           # MemoryStateStore
│   │   │   ├── sqlite_store.py           # SQLiteStateStore
│   │   │   └── checkpointer.py           # Checkpointer
│   │   │
│   │   └── event/                        # 事件系统
│   │       ├── __init__.py
│   │       ├── event_bus.py              # EventBus - 事件总线
│   │       ├── event_types.py            # 事件类型定义
│   │       └── event_handlers.py         # 事件处理器
│   │
│   ├── agents/                           # 智能体层
│   │   ├── __init__.py
│   │   ├── base.py                       # BaseAgent 抽象基类
│   │   ├── agent_factory.py              # AgentFactory - 智能体工厂
│   │   ├── planner.py                    # PlannerAgent
│   │   ├── analyzer.py                   # AnalyzerAgent
│   │   ├── matcher.py                    # MatcherAgent
│   │   ├── composer.py                   # ComposerAgent
│   │   └── plugin_agent.py               # PluginAgent - 插件代理
│   │
│   ├── domain/                           # 领域模型
│   │   ├── __init__.py
│   │   ├── entities/                     # 实体
│   │   │   ├── __init__.py
│   │   │   ├── video_asset.py            # VideoAsset
│   │   │   ├── segment.py                # Segment
│   │   │   ├── slot.py                   # Slot
│   │   │   ├── timeline.py               # Timeline
│   │   │   └── assembly_state.py         # AssemblyState
│   │   │
│   │   ├── value_objects/                # 值对象
│   │   │   ├── __init__.py
│   │   │   ├── intent.py                 # IntentType
│   │   │   ├── risk.py                   # RiskLevel
│   │   │   ├── capability.py             # CapabilityDeclaration
│   │   │   └── execution_result.py       # ExecutionResult
│   │   │
│   │   └── repositories/                 # 仓储接口
│   │       ├── __init__.py
│   │       ├── asset_repository.py       # AssetRepository
│   │       ├── project_repository.py     # ProjectRepository
│   │       └── session_repository.py     # SessionRepository
│   │
│   ├── services/                         # 服务层
│   │   ├── __init__.py
│   │   ├── llm_service.py                # LLMService - 策略模式
│   │   ├── clip_service.py               # CLIPService
│   │   ├── ffmpeg_service.py             # FFmpegService
│   │   ├── scene_detect_service.py       # SceneDetectService
│   │   ├── vector_service.py             # VectorService
│   │   └── file_service.py               # FileService
│   │
│   ├── infrastructure/                   # 基础设施
│   │   ├── __init__.py
│   │   ├── persistence/                  # 持久化
│   │   │   ├── __init__.py
│   │   │   ├── postgres_repository.py    # PostgreSQL 仓储
│   │   │   └── minio_repository.py       # MinIO 仓储
│   │   │
│   │   ├── cache/                        # 缓存
│   │   │   ├── __init__.py
│   │   │   ├── cache_service.py          # CacheService
│   │   │   └── redis_cache.py            # RedisCache
│   │   │
│   │   └── messaging/                    # 消息
│   │       ├── __init__.py
│   │       ├── message_queue.py          # MessageQueue
│   │       └── redis_queue.py            # RedisQueue
│   │
│   ├── api/                              # API 层
│   │   ├── __init__.py
│   │   ├── v1/                           # API v1
│   │   │   ├── __init__.py
│   │   │   ├── routes.py                 # 路由注册
│   │   │   ├── dependencies.py           # 依赖注入
│   │   │   ├── session.py                # 会话 API
│   │   │   ├── asset.py                  # 素材 API
│   │   │   ├── timeline.py               # 时间线 API
│   │   │   ├── export.py                 # 导出 API
│   │   │   └── webhook.py                # Webhook API
│   │   │
│   │   ├── middleware/                   # 中间件
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                   # 认证中间件
│   │   │   ├── logging.py                # 日志中间件
│   │   │   ├── rate_limit.py             # 限流中间件
│   │   │   └── error_handler.py          # 错误处理
│   │   │
│   │   ├── websocket/                    # WebSocket
│   │   │   ├── __init__.py
│   │   │   ├── connection_manager.py     # ConnectionManager
│   │   │   └── message_handler.py        # MessageHandler
│   │   │
│   │   └── schemas/                      # Pydantic 模型
│   │       ├── __init__.py
│   │       ├── request.py
│   │       ├── response.py
│   │       └── event.py
│   │
│   ├── cli/                              # CLI
│   │   ├── __init__.py
│   │   ├── main.py                       # CLI 入口
│   │   ├── commands.py                   # 命令定义
│   │   └── renderer.py                   # 输出渲染
│   │
│   └── plugins/                          # 插件系统
│       ├── __init__.py
│       ├── plugin_base.py                # PluginBase
│       ├── plugin_loader.py              # PluginLoader
│       ├── plugin_manager.py             # PluginManager
│       └── sandbox/                      # 沙箱
│           ├── __init__.py
│           └── docker_sandbox.py         # DockerSandbox
│
├── config/                               # 配置
│   ├── __init__.py
│   ├── settings.py                       # 全局配置
│   └── profiles/                         # 配置环境
│       ├── development.yaml
│       ├── production.yaml
│       └── testing.yaml
│
├── tests/                                # 测试
│   ├── __init__.py
│   ├── unit/                             # 单元测试
│   │   ├── core/
│   │   ├── agents/
│   │   ├── domain/
│   │   └── services/
│   │
│   ├── integration/                      # 集成测试
│   │
│   ├── e2e/                              # 端到端测试
│   │
│   └── fixtures/                         # 测试数据
│
├── scripts/                              # 脚本
│   ├── dev.py                            # 开发辅助
│   ├── seed_data.py                      # 数据填充
│   └── benchmark.py                      # 性能基准
│
├── docker/                               # Docker
│
├── docs/                                 # 文档
│
├── pyproject.toml
├── requirements.txt
├── .env.example
└── README.md
```

### 3.2 已实现模块清单

#### `api/` — HTTP API 层 (20 个路由端点)

| 文件 | 职责 | 路由前缀 |
|------|------|----------|
| `index_api.py` | 根路由 `/` + `/health` + `/config/styles` | 无 |
| `rest_api.py` | 核心业务: 分镜生成 / 批量处理 / 任务管理 | `/api/v1` |
| `function_calls.py` | V0.1 stub 类型定义 (14 个类型 + TaskFactory stub) | (非路由, 供 rest_api 导入) |

**完整 API 端点表：**

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 服务信息 |
| GET | `/health` | 健康检查 |
| GET | `/config/styles` | 支持的视频风格 |
| POST | `/api/v1/storyboard` | 分镜生成 (异步) |
| POST | `/api/v1/storyboard/sync` | 分镜生成 (同步) |
| POST | `/api/v1/storyboard/batch` | 批量分镜 (异步, ≤50) |
| POST | `/api/v1/storyboard/batch/sync` | 批量分镜 (同步, ≤20) |
| GET | `/api/v1/status/{task_id}` | 任务状态 |
| GET | `/api/v1/result/{task_id}` | 任务结果 |
| DELETE | `/api/v1/task/{task_id}` | 取消任务 |
| GET | `/api/v1/tasks` | 任务列表 |
| GET | `/api/v1/queue/status` | 队列状态 |
| GET | `/api/v1/stats` | 处理统计 |
| GET | `/api/v1/pending-tasks` | 未完成任务 |
| POST | `/api/v1/recover-tasks` | 手动任务恢复 |
| GET | `/api/v1/batch/status/{batch_id}` | 批量状态 |
| GET | `/api/v1/batch/result/{batch_id}` | 批量结果 |
| GET | `/api/v1/config` | 默认配置 |
| GET | `/api/v1/languages` | 支持的语言 |

#### `app/` — 应用装配

| 文件 | 职责 |
|------|------|
| `application.py` | FastAPI app 创建 + CORS + 中间件 + 生命周期 + 异常处理 |
| `proxy.py` | 反向代理路由 (localhost 文件服务) |
| `setup_env.py` | 环境设置引擎: venv 创建 / 依赖检测 / 自动安装 / 启动 |

#### `client/` — AI 客户端 (多供应商)

| 文件 | 供应商 |
|------|--------|
| `base_client.py` | 抽象基类 + HTTP 通用逻辑 |
| `ai_client.py` | 统一入口 `global_ai_client` → 按 config 路由到具体供应商 |
| `openai_client.py` | OpenAI 适配 |
| `qwen_client.py` | 通义千问 (DashScope) 适配 |
| `deepseek_client.py` | DeepSeek 适配 |
| `ollama_client.py` | Ollama 本地模型适配 |
| `openai_compat.py` | OpenAI 兼容模式 (vLLM 等) |
| `client_factory.py` | 客户端工厂 + 缓存 |

#### `tools/` — 视频分析工具 (6 个)

| 文件 | 功能 |
|------|------|
| `video_metadata_tool.py` | 视频元数据读取 (时长/分辨率/编码/帧率) |
| `scene_recognition_tool.py` | 场景切换检测 (直方图差值 + 自适应阈值) |
| `speech_recognition_tool.py` | 语音识别 (SpeechRecognition 封装) |
| `emotion_analysis_tool.py` | 情感分析 (基于文本关键词) |
| `object_detection_tool.py` | 目标检测 |
| `requirement_analyzer_tool.py` | 需求解析 Agent (关键字匹配, V0.2 替换为 LLM) |

#### `utils/` — 工具库 (15 个)

| 文件 | 功能 |
|------|------|
| `ffmpeg_utils.py` | FFmpeg 命令构建 (裁剪/合并/转码/滤镜) |
| `ffmpeg_env_utils.py` | FFmpeg 环境检测 (PATH/内置/自定义路径) |
| `ffmpeg_run_utils.py` | FFmpeg 进程执行 + 超时控制 |
| `file_utils.py` | 文件操作 + 资源路径解析 |
| `path_utils.py` | 项目根目录路径解析 |
| `hash_utils.py` | 哈希计算 (文件/字符串) |
| `dotenv_loader.py` | 多层级 .env 加载器 |
| `env_utils.py` | 环境变量 + ASCII 艺术字打印 |
| `log_utils.py` | 异常详情打印 + 堆栈帧分析 |
| `api_utils.py` | API 辅助函数 |
| `color_utils.py` | 颜色处理 |
| `console_colors.py` | 终端颜色常量 |
| `obj_utils.py` | 对象工具函数 |
| `redis_utils.py` | Redis 客户端封装 |
| `background_audio_utils.py` | 背景音频处理 |

#### `config/` — 配置

| 文件 | 职责 |
|------|------|
| `config.py` | 配置读取 + `Settings` 统一入口 + 默认配置 DEFAULT_CONFIG |
| `config.json` | 用户本地覆盖配置 |

---

## 4. V0.1 状态矩阵

### 4.1 已可用 (生产级)

| 模块 | 状态 |
|------|------|
| FastAPI 启动 + 热重载 + 多进程 | 完成 |
| CORS 中间件 + 异常处理 + 缓存头 | 完成 |
| 20 个 REST 端点骨架 | 完成 |
| 多 AI 供应商客户端 (OpenAI/Qwen/DeepSeek/Ollama) | 完成 |
| FFmpeg 命令构建 + 环境检测 + 执行 | 完成 |
| 视频元数据读取 | 完成 |
| 场景检测 (直方图) | 完成 |
| 语音识别 (SpeechRecognition) | 完成 |
| 日志系统 (控制台 + JSON + 文件) | 完成 |
| 虚拟环境自动创建 + 依赖安装 + 启动 | 完成 |
| Redis 客户端封装 | 完成 |
| 配置系统 (JSON + .env 双层) | 完成 |

### 4.2 V0.1 Stub (空实现, V0.2 完成)

| 模块 | 当前状态 |
|------|----------|
| `RequestContextMiddleware` | 直通, 无上下文注入 |
| `startup_with_recovery()` | 空函数, 不恢复任务 |
| `TaskFactory` (在 function_calls.py) | 空壳, submit/submit_and_wait/batch 均为 no-op |
| `TaskManager` (在 function_calls.py) | 空壳, 无实际状态存储 |
| `set_language()` | 空函数 |
| `ShotConfig` | 空 dataclass |
| `get_generate_video_prompt()` | 简单包装用户输入 |
| `get_user_requirement_prompt()` | 简单包装用户输入 |
| `RequirementAnalyzerTool` | 关键字匹配, 无 LLM 调用 |
| `list_tasks()` | 返回空列表 |
| 所有 `/stats` `/queue/status` | 返回空统计数据 |

### 4.3 空目录 (待实现)

| 目录 | 规划用途 | 目标版本 |
|------|----------|----------|
| `agents/` | Agent 实现 (clip_gen/audio_mix/subtitle/... ) | V0.3 |
| `hub/` | 中枢调度引擎 (意图路由 + 能力注册) | V0.2 |
| `prompts/` | Prompt 模板库 (分镜/配音/字幕/混剪) | V0.2 |
| `state/` | 全局状态管理 (工作流上下文) | V0.3 |
| `ui/` | Streamlit/Gradio 前端界面 | V0.3 |
| `tests/` | 测试用例 | V0.2 |
| `scripts/` | 运维脚本 | V0.2 |
| `docker/` | Docker 部署配置 | V0.3 |

---

## 5. 版本演进路线

```
V0.1 (当前)          V0.2              V0.3              V1.0           V2.0
  基础框架 ────────► LLM集成 ────────► 多Agent协作 ────► 产品化 ──────► 商业化
  ────────           ────────          ────────          ────────       ────────
  关键字命令         语义理解           能力注册           完整前端        多平台
  Stub类型          真实Task管理       状态持久化         用户系统        分布式
  FastAPI骨架       Prompt模板        工作流引擎         性能优化        API商业化
  FFmpeg封装        需求解析LLM       前端界面           Docker/K8s      监控运维
```

| 版本 | 核心交付 | 关键技术决策 |
|------|----------|--------------|
| V0.1 | 基础框架 + API 骨架 + 工具库 | FastAPI (非 Flask), 关键字解析 (非 LLM) |
| V0.2 | LLM 语义理解 + 真实任务管理 + Prompt 模板 | 接入 AI 客户端进行意图解析和需求分析 |
| V0.3 | 多 Agent 协作 + 工作流引擎 + 前端 | 星型中枢正式实现, Agent 注册机制 |
| V1.0 | 产品化 (完整前端 + 用户系统 + 性能优化) | 生产部署, Docker/K8s |
| V2.0 | 商业化 (多平台 + API 服务 + 监控运维) | SaaS 化 |

---

## 6. 开发约定

### 6.1 命名空间

所有 import 统一使用 `penclip.*` 前缀。**禁止**使用 `penshot.*` / `neopen.*` / `config.*` / `utils.*` 等旧前缀。

```python
# 正确
from penclip.logger import info, error
from penclip.config.config import settings
from penclip.utils.ffmpeg_utils import build_cut_command

# 错误
from penshot.logger import info
from neopen.config import settings
from utils.ffmpeg_utils import ...
```

### 6.2 日志

```python
from penclip.logger import debug, info, warning, error
# 仅用于高频/诊断型日志
debug("...")
# 标准业务流程
info("...")
# 可恢复异常
warning("...")
# 需要关注的错误
error("...")
```

### 6.3 工具创建模式 (Agent 开发用)

```python
# 1. 定义 DEFAULT_CONFIG
DEFAULT_CONFIG = {...}

# 2. 创建类
class MyTool:
    def __init__(self, config=None): ...

# 3. 全局实例
_my_tool = None

# 4. 便捷函数
def get_my_tool() -> MyTool:
    global _my_tool
    if _my_tool is None:
        _my_tool = MyTool()
    return _my_tool
```

### 6.4 数据流约定

```
用户请求 → FastAPI 端点 → TaskFactory.submit()
  → Hub (V0.2) → Agent → Tool → 返回结果
  → TaskFactory 更新状态 → 用户轮询/回调
```

### 6.5 配置访问

```python
from penclip.config.config import settings

# API 服务器配置
host = settings.api.host
port = settings.api.port

# 数据路径
paths = settings.get_data_paths()
# {"data_output": "data/output", "data_memory": "data/memory", ...}
```

---

## 7. 当前数据依赖

| 数据目录 | 用途 | 来源 |
|----------|------|------|
| `data/output/` | 视频输出 | 应用启动时自动创建 |
| `data/memory/` | Agent 记忆 | 应用启动时自动创建 |
| `data/embedding/` | 向量嵌入 | 应用启动时自动创建 |
| `data/templates/` | 模板文件 | 应用启动时自动创建 |
| `data/temp/` | 临时文件 | 按需创建 |
| `data/verify/` | 验证报告 | 按需创建 |
| `uploads/` | 用户上传 | 按需创建 |

---

## 8. 关键文件索引

高优先级文件（修改频率最高）：

- `main.py` — 启动入口
- `src/penclip/app/application.py` — FastAPI 应用装配
- `src/penclip/api/rest_api.py` — 核心业务路由 (822 lines, 最大文件)
- `src/penclip/api/function_calls.py` — 类型定义 + TaskFactory stub
- `src/penclip/config/config.py` — Settings + 默认配置
- `src/penclip/client/ai_client.py` — AI 统一入口
- `src/penclip/tools/requirement_analyzer_tool.py` — 需求解析 (V0.1 关键字, V0.2 LLM)
- `pyproject.toml` — 依赖声明

---

## 9. V0.2 待实现任务优先级

| 优先级 | 任务 | 依赖 |
|--------|------|------|
| P0 | 实现 `TaskFactory` / `TaskManager` 真实逻辑 | function_calls.py stub |
| P0 | 集成 LLM 到需求解析 (`RequirementAnalyzerTool`) | AI client 已完成 |
| P0 | 创建 Prompt 模板 (`prompts/`) | 无 |
| P1 | 实现 `hub/` 中枢调度引擎 | TaskFactory |
| P1 | 实现 `RequestContextMiddleware` 上下文注入 | 无 |
| P1 | 实现 `startup_with_recovery` 任务恢复 | Redis |
| P1 | 编写测试用例 (`tests/`) | 所有 P0 |
| P2 | 实现第一个真实 Agent (`agents/`) | Hub |
| P2 | Streamlit 前端 (`ui/`) | API |
| P2 | Docker 部署 (`docker/`) | 所有 P1 |

---

## 10. 启动命令

```bash
# 开发模式 (热重载 + 单进程)
python main.py

# 自定义端口
python main.py --port 8080

# 多进程 (生产, 需要 Redis)
python main.py --port 8000 --host 0.0.0.0
# 在 config.json 中设置 flask.workers > 1

# 验证导入
python -c "import penclip; print(penclip.__version__)"
python -c "from penclip.config.config import settings; print(settings.api.host, settings.api.port)"
python -c "from penclip.app import app; print(app.title)"
```
