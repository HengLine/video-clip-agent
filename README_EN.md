# NeoClip — AI Video Mix Clipping Agent

An AI video mix clipping system built on a **star-hub dispatch architecture**. It drives video analysis, segment matching, and automatic composition from natural language, delivering a "human-in-the-loop" creative experience through multi-agent collaboration — AI assists rather than replaces the creator.

## Architecture Overview

NeoClip follows a **DDD layered architecture** with a **star-hub dispatch pattern** at the top (`CentralHub` handles command parsing → intent recognition → capability routing → agent dispatch). The first registered standard workflow is a **linear chain** (sampling → parsing → analysis → matching → composition).

```
User input → CentralHub → [intent recognition → risk assessment → capability routing] → Agent execution → state update → user feedback
```

Layered structure (dependency direction: outer → inner, inner has zero reverse dependencies):

| Layer | Directory | Responsibility |
| :-- | :-- | :-- |
| Domain | `domain/` | Entities (Pydantic) + value objects (dataclass/enum) + repository interfaces |
| Application | `core/` | Hub dispatch / orchestration / state / event bus |
| Agents | `agents/` | `BaseAgent` + Planner/Analyzer/Matcher/Composer |
| Services | `services/` | LLM/CLIP/FFmpeg/scene detection/vector search |
| Infrastructure | `infrastructure/` | PostgreSQL/MinIO/Redis repositories and caches |
| Interface | `api/` + `cli/` | REST v1 / middleware / WebSocket / CLI |

**Current version**: V0.1 (star-hub skeleton) — domain model and hub dispatch implemented; `LangGraph` orchestration, `services/`, and `infrastructure/` are mostly V0.2 stubs. See [Roadmap](#roadmap).

## Core Features

- **Interactive console (REPL)**: real-time human-in-the-loop — clarification dialogue, progressive refinement, and confirmation gates for high-risk operations
- **Star-hub dispatch**: command parsing → intent recognition (30+ intents) → risk assessment → capability routing
- **Capability registration**: extend functionality by subclassing `BaseAgent` and declaring capabilities — no hub code changes required
- **Multiple AI providers**: OpenAI / Qwen / DeepSeek / Ollama (local models)
- **Video processing**: scene detection, semantic annotation (CLIP), speech recognition, emotion analysis, object detection, FFmpeg composition
- **Structured logging**: leveled logs + JSON format + file rotation

## Quick Start

### Requirements

- Python 3.9+
- FFmpeg (on system PATH, or auto-detected by the project)

### Installation

```bash
git clone https://github.com/neopen/video-clip-agent.git
cd video-clip-agent

# Create a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate.bat
# Linux / macOS
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

> For development, install the full dev dependencies: `pip install -e ".[dev]"`

### Configure an AI Provider

Copy `.env.example` to `.env` and fill in your provider of choice:

```ini
# Provider: openai | qwen | deepseek | ollama
AI_PROVIDER=qwen

# Qwen (DashScope compatible mode)
QWEN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxx
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
```

Environment variables per provider:

| Provider | Environment variables |
| :-- | :-- |
| OpenAI | `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` |
| Qwen | `QWEN_API_KEY` / `QWEN_BASE_URL` / `QWEN_MODEL` |
| DeepSeek | `DEEPSEEK_API_KEY` / `DEEPSEEK_BASE_URL` / `DEEPSEEK_MODEL` |
| Ollama | `OLLAMA_BASE_URL` / `OLLAMA_MODEL` |

Configuration uses a **dual channel**: `config.json` (local user overrides) + `.env` (environment variables, higher priority).

### Start the Server

```bash
python main.py            # default http://localhost:8000
python main.py --port 8080
python main.py --host 0.0.0.0 --port 8000   # production (multi-process needs Redis)
```

Once started, the interactive API docs are at http://localhost:8000/docs.

### Start the Interactive Console (primary usage)

NeoClip uses the **interactive console** as its primary interface (REST async is only a fallback):

```bash
# Interactive console (requires: pip install -e .)
neoclip-cli                       # auto-generated session
neoclip-cli --session my-vlog     # specify a session ID

# Or via module (development)
python -m neoclip.cli.main
```

The console supports three interaction modes (one-shot commands / clarification dialogue / progressive refinement) plus confirmation gates for high-risk operations:

```
neoclip> make a travel vlog, scenery first, food in the middle
Confirm creating a new timeline plan from this request?
Confirm? [y/N] y
[OK] Created timeline with 3 slot(s)

neoclip> render the final video
Confirm starting the final render? Cancelling mid-render may leave incomplete output.
Confirm? [y/N] y
[OK] Video rendered to data/output/output.mp4

neoclip> exit
```

> See the [console usage guide](docs/视频混剪智能体-控制台使用指南.md) (Chinese) for full details.

## API Reference

### Available Endpoints

System (`index_api.py`):

| Method | Path | Description |
| :-- | :-- | :-- |
| GET | `/` | Service info |
| GET | `/health` | Health check |

Domain routes (`api/v1/`, prefix `/api/v1`):

| Method | Path | Description |
| :-- | :-- | :-- |
| POST | `/api/v1/tasks` | Submit a natural-language instruction (async, returns task_id) |
| GET | `/api/v1/tasks/{task_id}` | Get task status |
| GET | `/api/v1/tasks/{task_id}/result` | Get task result |
| DELETE | `/api/v1/tasks/{task_id}` | Cancel a task |
| POST | `/api/v1/sessions` | Create a session |
| GET | `/api/v1/sessions/{session_id}` | Get a session |
| DELETE | `/api/v1/sessions/{session_id}` | Delete a session |
| POST | `/api/v1/assets` | Upload/register an asset |
| GET | `/api/v1/assets/{asset_id}` | Get an asset |
| GET | `/api/v1/assets/{asset_id}/metadata` | Asset metadata |
| POST | `/api/v1/assets/{asset_id}/analyze` | Analyze an asset |
| POST | `/api/v1/timelines` | Create a timeline |
| GET | `/api/v1/timelines/{timeline_id}` | Get a timeline |
| PUT | `/api/v1/timelines/{timeline_id}/slots/{slot_id}` | Update a slot |
| POST | `/api/v1/exports/render` | Start a render export |
| GET | `/api/v1/exports/{task_id}/status` | Render status |
| GET | `/api/v1/exports/{task_id}/download` | Download result |
| POST | `/api/v1/webhooks` | Register a webhook |
| DELETE | `/api/v1/webhooks/{webhook_id}` | Delete a webhook |

### Usage Example

```bash
# Health check
curl http://localhost:8000/health

# Submit a natural-language instruction (async)
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Cut the funny parts into a highlight reel", "language": "zh"}'
# → {"task_id": "...", "session_id": "...", "status": "pending"}

# Query task status / result
curl http://localhost:8000/api/v1/tasks/{task_id}
curl http://localhost:8000/api/v1/tasks/{task_id}/result
```

> Interactive API docs: http://localhost:8000/docs. The REST async API is a **fallback**; for the primary interaction experience use the [interactive console](docs/视频混剪智能体-控制台使用指南.md).

## Directory Structure

See [`.claude/skills/project.md`](.claude/skills/project.md) for the full structure; brief overview:

```
src/neoclip/
├── domain/          # Domain layer: entities / value_objects / repositories (zero deps)
├── core/            # Application layer: hub / orchestration / state / event
├── agents/          # Agents: BaseAgent + Planner/Analyzer/Matcher/Composer
├── services/        # Services: llm / clip / ffmpeg / scene_detect / vector / file
├── infrastructure/  # Infrastructure: persistence / cache / messaging
├── api/             # Interface: v1 / middleware / websocket / schemas
├── cli/             # CLI (interactive console)
├── plugins/         # Plugin system + Docker sandbox
├── hub/ graph/ state/   # ⚠️ Bridge compatibility layer (points to core/, domain/)
├── client/          # Legacy: multi AI provider clients
├── tools/           # Legacy: 6 video analysis tools
└── utils/ config/ logger.py   # Legacy: utilities / config / logging
```

## Tech Stack

- **Language**: Python 3.9+
- **Web**: FastAPI + uvicorn (async, auto OpenAPI docs)
- **AI**: OpenAI / Qwen / DeepSeek / Ollama, LangGraph 1.x + LangGraph Checkpoint
- **Video**: FFmpeg, OpenCV, PyDub; SpeechRecognition
- **Data**: NumPy, Pandas, Scikit-learn
- **Queue/Cache**: Redis (multi-process mode)
- **Code quality**: ruff, black, mypy, pytest, pre-commit

## Roadmap

| Version | Codename | Core goal | Status |
| :-- | :-- | :-- | :-- |
| V0.1 | Star-hub skeleton | DDD layered skeleton + keyword command parsing | **Current** |
| V0.2 | Semantic understanding | LLM intent parsing + real LangGraph orchestration + SQLite state | Planned |
| V0.3 | Visual collaboration | Web UI + multi-agent collaboration + formalized capability registration | Planned |
| V1.0 | Production-ready | Enterprise capabilities (auth/rate-limit/Postgres/MinIO/K8s) | Future |
| V2.0 | Open ecosystem | Plugin marketplace + Docker sandbox | Future |

## Development

```bash
# Code formatting
black src/ tests/

# Lint check and auto-fix
ruff check src/ tests/
ruff check --fix src/ tests/

# Type checking
mypy src/neoclip

# Run tests
pytest

# Git hooks (pre-commit checks)
pre-commit install
```

## Documentation

| Document | Description |
| :-- | :-- |
| [Console usage guide](docs/视频混剪智能体-控制台使用指南.md) | Full interactive console (REPL) usage (Chinese) |
| [Quick start](docs/视频混剪智能体-快速开始.md) | Illustrated from-zero-to-running guide (Chinese) |
| [Project summary](docs/视频混剪智能体-项目总结.md) | Design philosophy and core contracts (Chinese) |
| [Design principles](docs/视频混剪智能体-设计原则.md) | Target architecture and design patterns (Chinese) |
| [Technical architecture](docs/视频混剪智能体-技术架构.md) | System architecture, human-in-the-loop, data contracts (Chinese) |
| [Version evolution](docs/视频混剪智能体-版本演进.md) | Version planning and roadmap (Chinese) |
| [AI development overview](docs/AI开发导向-项目总览.md) | Project overview from an AI developer's perspective (Chinese) |
| [Project skills](.claude/skills/SKILL.md) | Claude Code skills index (Chinese) |

## License

[MIT](LICENSE)
