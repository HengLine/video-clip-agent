# 视频混剪智能体

一个基于智能体协作的视频混剪处理系统，能够根据用户的需求自动分析视频内容、编辑视频片段并输出最终结果。

## 系统架构

系统采用智能体协作架构，包含四个核心智能体：

1. **编排器智能体 (OrchestratorAgent)** - 负责解析用户需求，协调其他智能体工作
2. **内容分析智能体 (ContentAnalyzerAgent)** - 分析视频内容，生成剪切点
   1. **语音文字识别** : 将视频中的语音转换为文字，便于内容理解
   2. **物品场景检测** : 识别视频中的物体、场景和活动
   3. **情绪分析** : 分析视频内容的情感色彩，辅助剪辑决策
3. **视频编辑智能体 (VideoEditorAgent)** - 根据剪切点和用户需求进行视频编辑
4. **质量验证智能体 (QualityValidatorAgent)** - 验证最终视频的质量和符合度

智能体之间通过有向无环图(DAG)进行协作，确保处理流程的清晰和高效。

## 快速开始

### 环境要求

- Python 3.9+
- 足够的磁盘空间用于存储视频文件
- 安装FFmpeg（用于视频处理）

### 安装步骤

1. 安装Git、Python 和 FFmpeg（配置环境变量）

2. 克隆项目到本地

   ```sql
   git clone https://github.com/HengLine/video-clip-agent.git
   ```

3. 配置环境、安装依赖包：

   ```sh
   >> cd video-clip-agent
   
   >> python -m venv .venv
   >> .\venv\Scripts\activate.bat
   
   >> pip install -r requirements.txt
   ```
3. 配置LLM

   复制 .env.example 为 .env。并修改其中LLM内容

   ```ini
   # AI 提供商选择，可选值: openai, qwen, deepseek, ollama
   AI_PROVIDER=qwen
   
   # 文心一言配置
   QWEN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxx
   QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
   ```

4. 启动服务：

   ```sh
   >> python start_app.py
   ```

服务将在 http://localhost:8000 运行

### 处理视频 API

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

## 效果展示

输入示例

<img src="./source/image/%E8%BE%93%E5%85%A5%E7%A4%BA%E4%BE%8B.PNG" alt="输入示例" style="zoom:57%;" />

输出结果：

<img src="./source/image/%E8%BE%93%E5%87%BA%E7%BB%93%E6%9E%9C.PNG" alt="输出结果" style="zoom:67%;" />

## 注意事项

1. 上传的视频文件大小建议不超过200MB
2. 处理大文件可能需要较长时间，请耐心等待
3. 系统会自动清理15天前的日志文件，但不会自动清理上传和输出的视频文件
