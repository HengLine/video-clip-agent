# PenClip — 视频混剪智能体

基于**星型中枢分发架构**的 AI 视频混剪系统。以自然语言驱动视频分析、片段匹配与自动合成，通过多智能体协作实现「人机协同」的创作体验—— AI 辅助而非替代创作者。

## 架构概览

PenClip 采用 **DDD 分层架构**，顶层为**星型中枢分发模式**（`CentralHub` 负责命令解析 → 意图识别 → 能力路由 → 智能体调度），首个注册的标准工作流为**线性链路节点模式**（采样 → 解析 → 分析 → 匹配 → 合成）。

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

- **交互式控制台（REPL）**：实时人机协同——澄清式对话、渐进式细化、高风险操作确认中断
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

### 启动交互控制台（主要使用方式）

PenClip 以**控制台实时交互**为主要使用方式（REST 异步仅为备用）：

```bash
# 交互式控制台（需先 pip install -e .）
penclip-cli                       # 自动生成会话
penclip-cli --session my-vlog     # 指定会话 ID

# 或模块方式（开发环境）
python -m penclip.cli.main
```

控制台支持三种交互模式（一次性指令 / 澄清式对话 / 渐进式细化）与高风险操作确认中断。示例：

```
penclip> 做一个旅行 Vlog，风景放开头，美食放中间
确认根据此需求创建新的时间线规划？
确认执行? [y/N] y
[OK] Created timeline with 3 slot(s)

penclip> 最终渲染
确认开始最终渲染？渲染开始后中途取消可能导致不完整输出。
确认执行? [y/N] y
[OK] Video rendered to data/output/output.mp4

penclip> exit
```

> 完整用法见 [控制台使用指南](docs/视频混剪智能体-控制台使用指南.md)。

## API 接口

### 已上线端点

系统（`index_api.py`）：

| 方法 | 路径 | 说明 |
| :-- | :-- | :-- |
| GET | `/` | 服务信息 |
| GET | `/health` | 健康检查 |

领域路由（`api/v1/`，前缀 `/api/v1`）：

| 方法 | 路径 | 说明 |
| :-- | :-- | :-- |
| POST | `/api/v1/tasks` | 提交自然语言指令（异步，返回 task_id） |
| GET | `/api/v1/tasks/{task_id}` | 查询任务状态 |
| GET | `/api/v1/tasks/{task_id}/result` | 获取任务结果 |
| DELETE | `/api/v1/tasks/{task_id}` | 取消任务 |
| POST | `/api/v1/sessions` | 创建会话 |
| GET | `/api/v1/sessions/{session_id}` | 查询会话 |
| DELETE | `/api/v1/sessions/{session_id}` | 删除会话 |
| POST | `/api/v1/assets` | 上传/注册素材 |
| GET | `/api/v1/assets/{asset_id}` | 查询素材 |
| GET | `/api/v1/assets/{asset_id}/metadata` | 素材元数据 |
| POST | `/api/v1/assets/{asset_id}/analyze` | 分析素材 |
| POST | `/api/v1/timelines` | 创建时间线 |
| GET | `/api/v1/timelines/{timeline_id}` | 查询时间线 |
| PUT | `/api/v1/timelines/{timeline_id}/slots/{slot_id}` | 更新槽位 |
| POST | `/api/v1/exports/render` | 发起渲染导出 |
| GET | `/api/v1/exports/{task_id}/status` | 渲染状态 |
| GET | `/api/v1/exports/{task_id}/download` | 下载结果 |
| POST | `/api/v1/webhooks` | 注册 Webhook |
| DELETE | `/api/v1/webhooks/{webhook_id}` | 删除 Webhook |

### 使用示例

```bash
# 健康检查
curl http://localhost:8000/health

# 提交自然语言指令（异步）
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"user_input": "将视频中笑的部分剪成欢快的集锦", "language": "zh"}'
# → {"task_id": "...", "session_id": "...", "status": "pending"}

# 查询任务状态 / 结果
curl http://localhost:8000/api/v1/tasks/{task_id}
curl http://localhost:8000/api/v1/tasks/{task_id}/result
```

> 交互式 API 文档：http://localhost:8000/docs。REST 异步为**备用方案**，主要交互方式请使用[交互控制台](docs/视频混剪智能体-控制台使用指南.md)。

## 目录结构

完整目录结构与模块说明见 [`.claude/skills/project.md`](.claude/skills/project.md)，简要总览：

```
src/penclip/
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
mypy src/penclip

# 运行测试
pytest

# Git 钩子（提交前自动检查）
pre-commit install
```

## 文档

| 文档 | 说明 |
| :-- | :-- |
| [控制台使用指南](docs/视频混剪智能体-控制台使用指南.md) | 交互式控制台（REPL）完整用法 |
| [快速开始](docs/视频混剪智能体-快速开始.md) | 从零到跑通的图文指南 |
| [项目总结](docs/视频混剪智能体-项目总结.md) | 项目设计理念与核心契约 |
| [设计原则](docs/视频混剪智能体-设计原则.md) | 目标架构与设计模式 |
| [技术架构](docs/视频混剪智能体-技术架构.md) | 系统总体架构、人机协同、数据契约 |
| [版本演进](docs/视频混剪智能体-版本演进.md) | 版本规划与路线 |
| [AI 开发总览](docs/AI开发导向-项目总览.md) | AI 开发者视角的项目总览 |
| [项目技能](.claude/skills/SKILL.md) | Claude Code 技能文档索引 |

## License

[MIT](LICENSE)