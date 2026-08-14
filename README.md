# NeoClip — 视频混剪智能体

基于**星型中枢分发架构**的 AI 视频混剪系统。以自然语言驱动视频分析、片段匹配与自动合成，通过多智能体协作实现「人机协同」的创作体验—— AI 辅助而非替代创作者。

## 架构概览

NeoClip 采用 **DDD 分层架构**，顶层为**星型中枢分发模式**（`CentralHub` 负责命令解析 → 意图识别 → 能力路由 → 智能体调度），首个注册的标准工作流为**线性链路节点模式**（采样 → 解析 → 分析 → 匹配 → 合成）。

```
用户输入 → CentralHub → [意图识别 → 风险评估 → 能力路由] → Agent 执行 → 状态更新 → 用户反馈
```

分层结构（依赖方向：外层 → 内层，内层零反向依赖）：

| 层 | 目录 | 职责 |
| :-- | :-- | :-- |
| 领域层 | `domain/` | 实体（Pydantic）+ 值对象（dataclass/enum）+ 仓储接口 |
| 应用层 | `core/` | 中枢分发 / 编排 / 状态管理 / 事件总线 |
| 智能体 | `agents/` | `BaseAgent` + Planner/Analyzer/Matcher/Composer |
| 服务层 | `services/` | LLM/CLIP/FFmpeg/场景分割/向量检索 |
| 基础设施 | `infrastructure/` | PostgreSQL/MinIO/Redis 等仓储与缓存 |
| 接入层 | `api/` + `cli/` | REST v1 / 中间件 / WebSocket / CLI |

**当前版本**：V0.1（星型骨架）—— 领域模型与中枢分发已实现，`LangGraph` 编排、`services/`、`infrastructure/` 多为 V0.2 占位 stub。详见 [版本路线](#版本路线)。

## 核心特性

- **星型中枢分发**：命令解析 → 意图识别（30+ 意图枚举）→ 风险评估 → 能力路由
- **能力注册机制**：新增功能继承 `BaseAgent` 并声明能力，无需修改中枢代码
- **多 AI 提供商**：OpenAI / 通义千问 Qwen / DeepSeek / Ollama（本地模型）
- **视频处理**：场景检测、语义标注（CLIP）、语音识别、情绪分析、物体检测、FFmpeg 合成
- **结构化日志**：分级日志 + JSON 格式 + 文件轮转

## 快速开始

### 环境要求

- Python 3.9+
- FFmpeg（需配置到系统 PATH，或由项目内置检测）

### 安装

```bash
git clone https://github.com/neopen/video-clip-agent.git
cd video-clip-agent

# 创建虚拟环境
python -m venv .venv
# Windows
.venv\Scripts\activate.bat
# Linux / macOS
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

> 开发环境可安装完整开发依赖：`pip install -e ".[dev]"`

### 配置 AI 提供商

复制 `.env.example` 为 `.env`，选择并填写对应的提供商配置：

```ini
# 提供商: openai | qwen | deepseek | ollama
AI_PROVIDER=qwen

# 通义千问（DashScope 兼容模式）
QWEN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxx
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
```

各提供商对应的环境变量：

| 提供商 | 环境变量 |
| :-- | :-- |
| OpenAI | `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` |
| Qwen | `QWEN_API_KEY` / `QWEN_BASE_URL` / `QWEN_MODEL` |
| DeepSeek | `DEEPSEEK_API_KEY` / `DEEPSEEK_BASE_URL` / `DEEPSEEK_MODEL` |
| Ollama | `OLLAMA_BASE_URL` / `OLLAMA_MODEL` |

配置采用**双通道**：`config.json`（用户本地覆盖）+ `.env`（环境变量，优先级更高）。

### 启动服务

```bash
python main.py            # 默认 http://localhost:8000
python main.py --port 8080
python main.py --host 0.0.0.0 --port 8000   # 生产（多进程需 Redis）
```

服务启动后，交互式 API 文档位于 http://localhost:8000/docs。

## API 接口

### 已上线端点

核心业务（`rest_api.py`，前缀 `/api/v1`）：

| 方法 | 路径 | 说明 |
| :-- | :-- | :-- |
| POST | `/api/v1/storyboard` | 分镜生成（异步） |
| POST | `/api/v1/storyboard/sync` | 分镜生成（同步） |
| POST | `/api/v1/storyboard/batch` | 批量分镜（异步，≤50） |
| POST | `/api/v1/storyboard/batch/sync` | 批量分镜（同步，≤20） |
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

系统（`index_api.py`）：

| 方法 | 路径 | 说明 |
| :-- | :-- | :-- |
| GET | `/` | 服务信息 |
| GET | `/health` | 健康检查 |
| GET | `/config/styles` | 支持的视频风格 |

### 使用示例

```bash
# 健康检查
curl http://localhost:8000/health

# 分镜生成（异步）
curl -X POST http://localhost:8000/api/v1/storyboard \
  -H "Content-Type: application/json" \
  -d '{"script": "将视频中笑的部分剪成欢快的集锦", "language": "zh"}'

# 查询任务状态
curl http://localhost:8000/api/v1/status/{task_id}
```

> 新增的 `api/v1/` 领域路由（`session`/`asset`/`timeline`/`export`/`webhook`）已定义但**尚未挂载**到应用（`application.py` 未 include 该 router），当前返回占位 stub。

## 目录结构

完整目录结构与模块说明见 [`.claude/skills/project.md`](.claude/skills/project.md)，简要总览：

```
src/neoclip/
├── domain/          # 领域层：entities / value_objects / repositories（零依赖）
├── core/            # 应用层：hub / orchestration / state / event
├── agents/          # 智能体：BaseAgent + Planner/Analyzer/Matcher/Composer
├── services/        # 服务层：llm / clip / ffmpeg / scene_detect / vector / file
├── infrastructure/  # 基础设施：persistence / cache / messaging
├── api/             # 接入层：v1 / middleware / websocket / schemas
├── cli/             # CLI
├── plugins/         # 插件系统 + Docker 沙箱
├── hub/ graph/ state/   # ⚠️ Bridge 兼容转发层（指向 core/、domain/）
├── client/          # 遗留：多 AI 提供商客户端
├── tools/           # 遗留：6 个视频分析工具
└── utils/ config/ logger.py   # 遗留：工具库 / 配置 / 日志
```

## 技术栈

- **语言**：Python 3.9+
- **Web**：FastAPI + uvicorn（异步，自动 OpenAPI 文档）
- **AI**：OpenAI / Qwen / DeepSeek / Ollama，LangGraph 1.x + LangGraph Checkpoint
- **视频**：FFmpeg、OpenCV、PyDub；语音识别 SpeechRecognition
- **数据**：NumPy、Pandas、Scikit-learn
- **队列/缓存**：Redis（多进程模式）
- **代码质量**：ruff、black、mypy、pytest、pre-commit

## 版本路线

| 版本 | 代号 | 核心目标 | 状态 |
| :-- | :-- | :-- | :-- |
| V0.1 | 星型骨架 | DDD 分层骨架 + 关键词命令解析 | **当前** |
| V0.2 | 语义理解 | LLM 意图解析 + 真实 LangGraph 编排 + SQLite 状态 | 规划中 |
| V0.3 | 可视化协作 | Web UI + 多 Agent 协作 + 能力注册正式化 | 规划中 |
| V1.0 | 生产就绪 | 企业级能力（认证/限流/Postgres/MinIO/K8s） | 远期 |
| V2.0 | 生态开放 | 插件市场 + Docker 沙箱 | 远期 |

## 开发

```bash
# 代码格式化
black src/ tests/

# Lint 检查与自动修复
ruff check src/ tests/
ruff check --fix src/ tests/

# 类型检查
mypy src/neoclip

# 运行测试（当前 tests/ 为空，V0.2 待补充）
pytest

# Git 钩子（提交前自动检查）
pre-commit install
```

## 文档

| 文档 | 说明 |
| :-- | :-- |
| [设计原则](docs/视频混剪智能体-设计原则.md) | 目标架构与设计模式 |
| [技术架构](docs/视频混剪智能体-技术架构.md) | 系统总体架构、人机协同、数据契约 |
| [版本演进](docs/视频混剪智能体-版本演进.md) | 版本规划与路线 |
| [AI 开发总览](docs/AI开发导向-项目总览.md) | AI 开发者视角的项目总览 |
| [项目技能](.claude/skills/SKILL.md) | Claude Code 技能文档索引 |

## License

[MIT](LICENSE)