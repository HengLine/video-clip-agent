---
name: agent-development
description: PenClip agent and tool development — BaseAgent pattern, capability registration, intent types, AI client usage, services, and workflow integration. Use when adding a new agent, tool, capability, or service.
type: reference
---

# PenClip 智能体开发

## 架构原则

1. **所有新能力通过注册机制接入中枢**，不修改中枢代码（开闭原则）
2. **依赖倒置**：Agent 依赖 `BaseAgent` 抽象，不依赖具体中枢实现
3. **值对象用 dataclass，实体用 Pydantic**：`CapabilityDeclaration`/`ExecutionResult` 是 dataclass，业务实体是 Pydantic
4. **领域层零依赖**：Agent 不得 import `services/`、`infrastructure/` 的实现类

## 创建新 Agent（V0.1 标准模式）

继承 `BaseAgent`（模板方法模式），实现两个抽象方法：`declare_capabilities()` + `execute()`。参考 `src/penclip/agents/planner.py`。

```python
"""Agent 功能的一句话描述"""
from typing import Any, Dict, List, Optional

from penclip.agents.base import BaseAgent, ExecutionContext
from penclip.domain.value_objects.capability import CapabilityDeclaration
from penclip.domain.value_objects.execution_result import ExecutionResult
from penclip.domain.value_objects.intent import IntentType
from penclip.domain.value_objects.risk import RiskLevel
from penclip.logger import info

DEFAULT_CONFIG = {
    "max_slots": 20,
    "default_duration": 5.0,
}

class MyAgent(BaseAgent):
    agent_id = "my_agent"          # 唯一标识
    agent_name = "MyAgent"
    version = "0.1.0"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = {**DEFAULT_CONFIG, **(config or {})}
        super().__init__(config=cfg)

    def declare_capabilities(self) -> CapabilityDeclaration:
        return CapabilityDeclaration(
            name="my_capability",
            intents=[IntentType.PLAN_CREATE, IntentType.CLIP_TRIM],
            description="一句话说明能力",
            input_schema={"instruction": {"type": "string", "description": "自然语言指令"}},
            output_schema={"result": {"type": "object"}},
            risk_level=RiskLevel.MEDIUM,
            version=self.version,
            agent_id=self.agent_id,
        )

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        instruction = params.get("raw_text", "") or params.get("instruction", "")
        # 核心业务逻辑
        return ExecutionResult(
            success=True,
            data={"result": instruction},
            message="执行成功",
        )

# 单例 + 获取函数（与全局单例模式一致）
_my_agent: MyAgent = None

def get_my_agent() -> MyAgent:
    global _my_agent
    if _my_agent is None:
        _my_agent = MyAgent()
    return _my_agent
```

### 可选覆写方法

| 方法 | 用途 |
| :-- | :-- |
| `execute_incremental(params, context)` | 支持增量操作的 Agent 覆写（默认调用 `execute`） |
| `on_load()` / `on_unload()` | Agent 被中枢加载/卸载时的钩子 |
| `_validate_params(params)` | 参数校验（默认返回 True） |
| `_log_execution(result)` | 执行结果日志 |

## 注册到中枢

```python
from penclip.hub.hub_core import get_hub          # 或 penclip.core.hub.central_hub
from penclip.agents.my_agent import get_my_agent

hub = get_hub()
hub.register_agent(get_my_agent())                 # 自动读取 declare_capabilities()
hub.get_capabilities()                             # 查看已注册能力
```

注册流程：`register_agent` → 读取 `declare_capabilities()` → 写入 `CapabilityRegistry`（意图→能力名倒排索引）→ 发布 `CAPABILITY_REGISTERED` 事件。

## 关键值对象契约

### IntentType（`domain/value_objects/intent.py`）
30+ 意图，6 类（详见 `project.md`）。未知输入经 `_missing_` 兜底为 `UNKNOWN`。新增意图需同步更新 `IntentRecognizer._KEYWORD_INTENT_MAP` 与 `RiskAssessor._INTENT_RISK_MAP`。

### CapabilityDeclaration（`domain/value_objects/capability.py`）
```python
@dataclass
class CapabilityDeclaration:
    name: str
    intents: List[IntentType] = field(default_factory=list)
    description: str = ""
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    version: str = "0.1.0"
    agent_id: Optional[str] = None
```

### ExecutionResult（`domain/value_objects/execution_result.py`）
```python
@dataclass
class ExecutionResult:
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str = ""
    suggestions: List[str] = field(default_factory=list)
    status: str = "completed"
    command_id: Optional[str] = None
```

### ExecutionContext（`agents/base.py`）
```python
@dataclass
class ExecutionContext:
    session_id: Optional[str] = None
    hub_state: Optional[Dict[str, Any]] = None
    user_preferences: Dict[str, Any] = field(default_factory=dict)
```

## 现有 Agent 清单

| Agent | agent_id | 能力 | 状态 |
| :-- | :-- | :-- | :-- |
| `PlannerAgent` | `planner` | 规划类意图，关键词槽位抽取 | ✅ 有逻辑 |
| `AnalyzerAgent` | `analyzer` | 分析类意图 | ⚠️ 骨架 |
| `MatcherAgent` | `matcher` | 素材匹配 | ⚠️ 骨架 |
| `ComposerAgent` | `composer` | 视频合成 | ⚠️ 骨架 |
| `PluginAgent` | `plugin` | 插件代理 | ⚠️ 骨架 |

> 注意：`agents/planner_agent.py` 是 Bridge 转发模块（`from penclip.agents.planner import ...`），真实实现在 `agents/planner.py`。`application.py` 的启动钩子仍通过旧路径 `planner_agent` 导入，故保留。

## 使用 AI 客户端（遗留 `client/`，仍在使用）

```python
from penclip.client.ai_client import AIClient, global_ai_client

client = global_ai_client                       # 或 AIClient()
client.set_provider("qwen")                     # openai | qwen | deepseek | ollama
result = client.analyze_user_requirement("用户需求")
config = client.generate_video_config("视频配置描述")
```

添加新 provider：
1. 创建 `src/penclip/client/{provider}_client.py`，继承 `BaseAIClient`
2. 实现 `create_chat_completion` / 响应转换
3. 在 `client_factory.py` 工厂方法注册

> V0.2 起 LLM 调用将统一走 `services/llm_service.py`（策略模式，`LLMService` 接口 + 各实现 + `LLMFactory`），`client/` 将逐步退役。新代码优先考虑 `services/llm_service`。

## 服务层（`services/`）

策略/适配器模式，供 Agent 与 API 调用：

| 服务 | 职责 | V0.1 状态 |
| :-- | :-- | :-- |
| `llm_service.py` | LLM 调用统一入口（策略模式） | 骨架 |
| `clip_service.py` | CLIP 零样本分类 | stub |
| `ffmpeg_service.py` | FFmpeg 封装 | 骨架 |
| `scene_detect_service.py` | 场景分割（PySceneDetect） | stub |
| `vector_service.py` | 向量检索（Milvus Lite） | stub |
| `file_service.py` | 文件存储 | 骨架 |

## 工具目录（遗留 `tools/`，仍在使用）

| 工具 | 类名 | 功能 |
| :-- | :-- | :-- |
| `requirement_analyzer_tool` | `RequirementAnalyzer` | 需求解析（V0.1 关键词，V0.2 LLM） |
| `video_metadata_tool` | `VideoMetadataReader` | 视频元数据（FFprobe） |
| `scene_recognition_tool` | `SceneRecognitionTool` | 场景切换检测（直方图） |
| `speech_recognition_tool` | `SpeechRecognizer` | 语音识别 |
| `emotion_analysis_tool` | `EmotionAnalyzer` | 情绪分析（关键词） |
| `object_detection_tool` | `ObjectDetector` | 目标检测 |

旧工具模式（`DEFAULT_CONFIG` + 类 + `get_{name}()` 单例 + 便捷函数）见 `code-standards.md`，仍在 `tools/` 生效。

## 创建新 Agent 的 Checklist

- [ ] 在 `src/penclip/agents/` 创建文件，继承 `BaseAgent`
- [ ] 定义 `agent_id`/`agent_name`/`version` 类属性 + `DEFAULT_CONFIG`
- [ ] 实现 `declare_capabilities()`（声明 name/intents/schema/risk_level）
- [ ] 实现 `execute()` 返回 `ExecutionResult`
- [ ] 创建 `get_{name}()` 单例函数
- [ ] 在 `agents/__init__.py` 导出（如需公开）
- [ ] 经 `get_hub().register_agent()` 接入中枢
- [ ] 使用 `penclip.logger` 记录关键节点
- [ ] 若新增 `IntentType`，同步更新 `IntentRecognizer`/`RiskAssessor` 映射

## 禁止事项

- 不要修改中枢代码来添加能力（走 `register_agent`）
- 不要直接在 Agent 中调用外部 API（经 `AIClient` 或 `services/llm_service`）
- 不要在 Agent 中处理 HTTP 请求/响应（那是 `api/` 层职责）
- 不要在 Agent 中硬编码文件路径（经 config 或参数传入）
- 领域层（`domain/`）不得 import `services/`/`infrastructure/`/`api/`
- 不要修改 Bridge 层（`hub/`/`graph/`/`state/`）来承载业务逻辑，改 `core/`/`domain/`