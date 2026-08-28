---
name: code-standards
description: PenClip Python 编码规范——分层依赖、类型、Pydantic、命名、导入、日志和错误处理。编写、审查或重构 Python 代码时使用；检查命令见 validation.md。
type: reference
---

# PenClip 代码规范

## 分层与依赖规则

依赖方向严格**外层 → 内层**，内层禁止反向 import 外层：

```
domain/  →  零依赖（最内层，实体 + 值对象 + 仓储接口）
core/    →  只能依赖 domain
agents/  →  依赖 domain + core
services/ →  依赖 domain（+ core）
infrastructure/ →  依赖 domain（实现仓储接口）
api/     →  依赖 core + services（最外层）
```

- `domain/` 不得 import `core/`、`services/`、`infrastructure/`、`api/`
- `infrastructure/` 实现 `domain/repositories/` 定义的接口（依赖倒置）
- 修改 Bridge 层（`hub/`、`graph/`、`state/` 顶层模块）不承载业务逻辑，只做转发

## dataclass vs Pydantic 选择

| 场景 | 用 | 理由 |
| :-- | :-- | :-- |
| 值对象（`CapabilityDeclaration`/`ExecutionResult`/`Event`） | `@dataclass` | 无行为的小对象，轻量 |
| 枚举（`IntentType`/`RiskLevel`/`TaskLifecycleStage`/`EventType`） | `Enum` | 有限取值集合 |
| 实体（`AssemblyState`/`Slot`/`Segment`/`VideoAsset`） | Pydantic `BaseModel` | 需校验/序列化/嵌套 |
| API 请求/响应 | Pydantic `BaseModel` | OpenAPI 自动文档 |

## 类型注解

- 所有公开函数必须有类型注解（参数 + 返回值）
- 使用 `typing` 模块的泛型：`Dict[str, Any]`、`List[int]`、`Optional[str]`
- 禁止使用 `Any` 作为参数/返回值类型（除非确实无法确定）
- 复杂类型使用 `TypeAlias` 声明别名

```python
from typing import Dict, Any, Optional, List

def process_video(video_path: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    ...
```

## Pydantic 数据模型

- API 请求/响应必须使用 Pydantic BaseModel
- 使用 `Field()` 添加校验约束（min_length, description 等）
- 使用 `field_validator` 实现自定义校验逻辑
- 所有字段默认有 description，用于自动生成 OpenAPI 文档

```python
from pydantic import BaseModel, Field, field_validator

class ProcessRequest(BaseModel):
    script: str = Field(..., min_length=1, description="原始剧本文本")
    language: str = Field(default="zh", description='语言代码')
    timeout: float = Field(default=300, ge=1, le=600, description="超时秒数")

    @field_validator("language")
    def validate_language(cls, v):
        if v not in {"zh", "en"}:
            raise ValueError("language must be 'zh' or 'en'")
        return v
```

## 命名规范

| 类型       | 规范                | 示例                          |
| :--------- | :------------------ | :---------------------------- |
| 模块文件   | snake_case          | `video_metadata_tool.py`      |
| 类名       | PascalCase          | `VideoMetadataReader`         |
| 函数/方法  | snake_case          | `read_metadata()`             |
| 常量       | UPPER_SNAKE_CASE    | `DEFAULT_CONFIG`              |
| 私有函数   | _前缀 + snake_case  | `_extract_key_metadata()`     |
| 私有属性   | _前缀（弱）        | `self._video_path`            |
| 全局单例   | global_ 前缀        | `global_ai_client`            |

## 模块结构规范

每个工具模块遵循统一结构：

```python
# 1. 文件头注释（可选的简洁说明）
"""模块功能的一句话描述"""

# 2. 标准库导入
import os
from typing import Dict, Any, Optional

# 3. 项目内部导入
from penclip.logger import debug, error

# 4. 常量/默认配置
DEFAULT_CONFIG = { ... }

# 5. 主类定义
class ClassName:
    def __init__(self, config=None): ...
    def method(self, ...) -> Dict[str, Any]: ...
    def _private_method(self, ...): ...

# 6. 全局实例
_instance = None

def get_instance() -> ClassName:
    global _instance
    if _instance is None:
        _instance = ClassName()
    return _instance

# 7. 便捷函数
def convenience_func(...) -> ...:
    return get_instance().method(...)
```

## 导入顺序

使用 ruff isort 规则自动排序，顺序为：
1. 标准库
2. 第三方库
3. 项目内部模块（`penclip.*`）

## 日志规范

```python
from penclip.logger import debug, info, warning, error

# 使用正确的级别
debug(f"调试信息，仅开发环境")
info(f"正常运行信息")
warning(f"可恢复的异常状态")
error(f"错误，需要关注")

# 不对日志字符串做 f-string 之前的大写控制
# 日志级别由 logger 配置统一管理
```

## docstring 规范

- 类和方法需要简洁的 docstring
- 使用 Google 风格（Args/Returns/Raises）
- 不写冗余描述（如"初始化方法"），只写非显而易见的逻辑

```python
def analyze(self, user_input: str) -> Dict[str, Any]:
    """分析用户需求
    
    Args:
        user_input: 用户输入的需求描述
        
    Returns:
        包含 success 标志和分析结果的字典
    """
```

## 错误处理

- 工具函数返回 Dict 带 success 字段，不抛异常
- API 层使用 HTTPException 向客户端返回错误
- 所有 try/except 必须记录日志
- 不吞噬异常：捕获后要么处理，要么重新抛出

```python
# 工具函数模式
def do_something(input: str) -> Dict[str, Any]:
    try:
        result = _inner_operation(input)
        return {'success': True, 'data': result}
    except Exception as e:
        error(f"操作失败: {e}")
        return {'success': False, 'error': str(e), 'data': None}

# API 层模式
try:
    result = tool.do_something(input)
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    return ProcessResult(success=True, data=result['data'])
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
```

## 环境变量

- 敏感信息（API Key）只能通过环境变量注入
- 使用 `python-dotenv` 加载 `.env` 文件
- 环境变量名使用 `UPPER_SNAKE_CASE`
- AI provider 相关命名：`{PROVIDER}_API_KEY`、`{PROVIDER}_BASE_URL`、`{PROVIDER}_MODEL`

## 禁止事项

- 不要在代码中硬编码 API Key 或密码
- 不要使用 `print()` 代替 logger
- 不要写超过 3 行的 docstring
- 不要引入未在 pyproject.toml 中声明的依赖
- 不要使用 `*` 导入 (`from module import *`)
- 函数参数不要超过 5 个（超过用配置对象封装）
