# NeoClip — 视频混剪智能体

基于星型中枢分发架构的 AI 视频混剪系统，通过智能体协作实现自然语言驱动的视频分析、片段匹配与自动合成。

## 架构概览

NeoClip 采用**星型中枢分发模式**作为顶层架构，**线性链路节点模式**作为中枢可调度的标准工作流：

> 用户输入 → 指令解析中枢 → 意图识别 → 路由分发 → 智能体执行 → 状态更新 → 用户反馈

**核心设计理念**：人机协同 — 系统规划、用户确认、增量迭代，AI 辅助而非替代创作者。

**当前版本**：V0.1（星型骨架 MVP）

## 快速开始

### 环境要求

- Python 3.9+
- FFmpeg（配置环境变量）
- 足够的磁盘空间存储视频文件

### 安装

```bash
git clone https://github.com/neopen/video-clip-agent.git
cd video-clip-agent

# 创建虚拟环境
python -m venv .venv
# Windows
.\venv\Scripts\activate.bat
# Linux/Mac
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 配置 LLM

复制 `.env.example` 为 `.env`，修改 AI 提供商配置：

```ini
# AI 提供商: openai, qwen, deepseek, ollama
AI_PROVIDER=qwen

# Qwen 配置
QWEN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxx
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 启动服务

```bash
python main.py
```

服务运行在 http://localhost:8000，API 文档在 http://localhost:8000/docs。

## API 接口

### 健康检查

```bash
curl http://localhost:8000/health
```

```json
{"status": "healthy"}
```

### 视频处理

**端点**: `/api/v1/storyboard`
**方法**: POST

```bash
curl -X POST http://localhost:8000/api/v1/storyboard \
  -H "Content-Type: application/json" \
  -d '{"script": "将视频中笑的部分剪成欢快的集锦", "language": "zh"}'
```

### 任务状态查询

```bash
curl http://localhost:8000/api/v1/status/{task_id}
```



## 版本路线

| 版本 | 代号     | 目标             |
| :--- | :------- | :--------------- |
| V0.1 | 星型骨架 | 验证技术闭环     |
| V0.2 | 语义理解 | LLM + 向量匹配   |
| V0.3 | 可视化   | Web UI + 协作    |
| V1.0 | 生产就绪 | 企业级服务       |
| V2.0 | 生态开放 | 插件市场         |

## 技术栈

- **语言**: Python 3.9+
- **Web**: FastAPI + uvicorn
- **AI**: OpenAI / Qwen / DeepSeek / Ollama
- **视频**: FFmpeg, OpenCV, PyDub
- **数据**: NumPy, Pandas, Scikit-learn
- **代码质量**: ruff, black, mypy, pre-commit

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 代码检查
ruff check src/ tests/
black --check src/ tests/
mypy src/neoclip

# 运行测试
pytest
```

## 文档

- [技术架构](docs/视频混剪智能体-技术架构.md)
- [版本演进](docs/视频混剪智能体-版本演进.md)

## License

MIT
