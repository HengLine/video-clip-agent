# 视频工具智能体 (Tool Video Agent)

一个基于智能体协作的视频处理系统，能够根据用户需求自动分析视频内容、编辑视频片段并验证输出质量。

## 系统架构

系统采用智能体协作架构，包含四个核心智能体：

1. **编排器智能体 (OrchestratorAgent)** - 负责解析用户需求，协调其他智能体工作
2. **内容分析智能体 (ContentAnalyzerAgent)** - 分析视频内容，生成剪切点
3. **视频编辑智能体 (VideoEditorAgent)** - 根据剪切点和用户需求进行视频编辑
4. **质量验证智能体 (QualityValidatorAgent)** - 验证最终视频的质量和符合度

智能体之间通过有向无环图(DAG)进行协作，确保处理流程的清晰和高效。

## 快速开始

### 环境要求

- Python 3.8+
- 足够的磁盘空间用于存储视频文件
- 安装FFmpeg（用于视频处理）

### 安装步骤

1. 克隆项目到本地

2. 安装依赖包：
```bash
pip install -r requirements.txt
```

3. 启动服务：
```bash
python start_app.py
```

服务将在 http://localhost:8000 运行

## API 使用

### 处理视频

**端点**: `/api/process-video`
**方法**: POST
**请求格式**:
- `query`: 用户的查询描述
- `files[]`: 要上传的视频文件

**示例请求**:
```bash
curl -X POST -F "query=提取所有猫的片段并按时间顺序排列" -F "files[]=@/path/to/video1.mp4" -F "files[]=@/path/to/video2.mp4" http://localhost:8000/api/process-video
```

**响应格式**:
```json
{
  "status": "success",
  "message": "视频处理成功",
  "video_url": "/api/video/generated_video.mp4",
  "report": {
    "validation_results": {...},
    "total_clips": 5,
    "editing_actions": 10,
    "passed": true
  }
}
```

### 下载视频

**端点**: `/api/video/<filename>`
**方法**: GET

通过处理视频API返回的URL可以直接下载生成的视频文件。

### 健康检查

**端点**: `/api/health`
**方法**: GET

检查服务运行状态：
```bash
curl http://localhost:8000/api/health
```

## 项目结构

```
├── hengline/
│   ├── agent/             # 智能体模块
│   │   ├── __init__.py
│   │   ├── agent_state.py       # 状态管理
│   │   ├── orchestrator_agent.py # 编排器智能体
│   │   ├── content_analyzer_agent.py # 内容分析智能体
│   │   ├── video_editor_agent.py # 视频编辑智能体
│   │   ├── quality_validator_agent.py # 质量验证智能体
│   │   └── graph.py       # 智能体协作图
│   ├── utils/             # 工具模块
│   │   ├── config_utils.py # 配置工具
│   │   └── env_utils.py   # 环境工具
│   ├── flask/             # Flask相关文件
│   │   └── templates/     # 模板目录
│   ├── logger.py          # 日志系统
│   └── app_flask.py       # Flask应用入口
├── uploads/               # 上传的视频文件
├── outputs/               # 生成的视频文件
├── app_env.py             # 应用环境基类
├── start_app.py           # 启动脚本
└── requirements.txt       # 依赖列表
```

## 注意事项

1. 上传的视频文件大小建议不超过200MB
2. 处理大文件可能需要较长时间，请耐心等待
3. 系统会自动清理15天前的日志文件，但不会自动清理上传和输出的视频文件

## 许可证

MIT