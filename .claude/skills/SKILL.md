# NeoClip AI 操作手册 (SKILL.md)

> 本文档是 AI 助手理解和操作 NeoClip 视频混剪智能体系统的专属指南

## 📋 系统概览

NeoClip 是一个基于智能体协作的视频混剪处理系统，能够根据用户需求自动分析视频内容、编辑视频片段并输出最终结果。

### 核心特性
- **智能体协作架构**: 4个专用智能体通过 DAG（有向无环图）协同工作
- **多模态内容分析**: 语音识别、场景检测、情绪分析
- **自动化视频编辑**: 基于分析结果自动裁剪、排序、合并视频
- **质量验证机制**: 确保输出视频符合用户需求和质量标准
- **Flask API 服务**: 提供 RESTful API 接口

---

## 🏗️ 系统架构

### 技术栈
- **语言**: Python 3.9+
- **AI 框架**: LangChain 0.3.27, LangGraph 0.6.10
- **Web 框架**: Flask + Flask-CORS
- **视频处理**: FFmpeg, MoviePy, OpenCV, PyDub
- **语音识别**: SpeechRecognition, Librosa
- **深度学习**: Transformers, PyTorch
- **数据科学**: NumPy, Pandas, Scikit-learn

---

## 🤖 智能体系统

### 1. 需求分析智能体 (RequirementAnalyzerAgent)
**职责**: 解析用户需求，制定分析策略

**输入**:
- `query`: 用户的自然语言描述
- `video_files`: 上传的视频文件列表

**输出**:
- `requirement_analysis`: 结构化的需求分析结果
- `analysis_strategy`: 分析策略和重点关注方向
- `validated_videos`: 验证后的视频文件路径

**关键逻辑**:
- 提取用户意图（剪辑类型、风格偏好、时长要求等）
- 验证视频文件可用性
- 生成后续智能体的执行策略

### 2. 内容分析智能体 (ContentAnalyzerAgent)
**职责**: 深度分析视频内容，识别剪切点

**子工具**:
1. **语音文字识别 (SpeechRecognitionTool)**
   - 将视频语音转换为文字
   - 时间戳对齐
   - 支持中英文识别

2. **场景识别 (SceneRecognitionTool)**
   - 检测场景转换点
   - 识别场景类型（室内/室外/人物/风景等）
   - 生成场景标签

3. **物体检测 (ObjectDetectionTool)**
   - 识别视频中的物体和人物
   - 跟踪物体出现的时间段
   - 生成物体清单

4. **情绪分析 (EmotionAnalysisTool)**
   - 分析视频片段的情感色彩
   - 情绪分类：高兴、悲伤、紧张、平静等
   - 情绪强度评分

**输出**:
- `analysis_results`: 每个视频的详细分析结果
- `clip_points`: 推荐的剪切点列表
- `content_tags`: 内容标签和关键词

### 3. 视频编辑智能体 (VideoEditorAgent)
**职责**: 根据分析结果执行视频编辑操作

**编辑操作**:
- **裁剪 (Cut)**: 按剪切点裁剪视频片段
- **排序 (Sort)**: 按用户需求重新排列片段
- **合并 (Merge)**: 使用转场效果合并片段
- **调整 (Adjust)**: 调整亮度、对比度、速度等
- **音频处理**: 添加背景音乐、调整音量

**输出**:
- `final_video_path`: 生成的最终视频路径
- `editing_actions`: 执行的编辑动作日志
- `preview_clips`: 预览片段（可选）

### 4. 质量验证智能体 (QualityValidatorAgent)
**职责**: 验证输出视频的质量和符合度

**验证项**:
- 视频完整性检查
- 画质和音质评估
- 需求符合度验证
- 技术规格检查（分辨率、帧率、编码等）

**输出**:
- `validation_results`: 详细的验证报告
- `passed`: 是否通过验证
- `suggestions`: 改进建议

---

## 🔄 工作流程 (LangGraph DAG)

