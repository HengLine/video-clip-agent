---
name: validation
description: PenClip 代码质量校验——black、ruff、mypy、pytest 与 pre-commit。新增或修改 Python 代码、修复检查错误、提交前验证时使用。
type: reference
---

# PenClip 代码校验

## 代码质量工具栈

| 工具        | 用途           | 配置文件               |
| :---------- | :------------- | :--------------------- |
| ruff        | Lint + 排序    | `pyproject.toml`       |
| black       | 格式化         | `pyproject.toml`       |
| mypy        | 类型检查       | `pyproject.toml`       |
| pytest      | 测试           | `pyproject.toml`       |
| pre-commit  | Git 钩子       | `.pre-commit-config.yaml` |

## 使用边界

- 本文档只描述仓库当前可执行的代码检查与测试命令。
- 工具版本、规则和路径以 `pyproject.toml` 为准；文档示例不应替代配置文件。
- 测试代码位于 `tests/`，源码采用 `src/penclip` 布局。

## 快速命令

```bash
# 代码格式化
black src/ tests/

# Lint 检查
ruff check src/ tests/

# Lint 自动修复
ruff check --fix src/ tests/

# 类型检查
mypy src/penclip

# 运行测试
pytest

# 运行测试 + 覆盖率
pytest --cov=penclip --cov-report=term-missing

# 运行指定的测试
pytest tests/unit/test_intent.py -v

# 跳过慢测试
pytest -m "not slow"

# 只运行集成测试
pytest -m "integration"
```

## pre-commit 配置

文件：`.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-yaml
      - id: check-json
  - repo: https://github.com/psf/black
    hooks:
      - id: black
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    hooks:
      - id: ruff
```

**安装和运行**：
```bash
pre-commit install          # 安装 git hooks
pre-commit run --all-files  # 手动在所有文件上运行
```

## ruff 规则

`pyproject.toml` 中启用的规则集：

| 代码 | 含义                 |
| :--- | :------------------- |
| E    | pycodestyle errors   |
| W    | pycodestyle warnings |
| F    | pyflakes             |
| I    | isort（导入排序）    |
| C    | comprehensions       |
| B    | flake8-bugbear       |
| UP   | pyupgrade            |
| SIM  | flake8-simplify      |

**忽略的规则**：
- E501：行长度（由 black 处理）
- B008：函数参数默认值中执行函数调用
- C901：函数复杂度

## black 配置

```toml
[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311', 'py312']
```

行长度 100，覆盖 Python 3.9-3.12。

## mypy 配置

```toml
[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
```

注意：`disallow_untyped_defs = false`（当前阶段不强制所有函数有完整类型注解）。

## pytest 配置

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
```

**测试标记**：
- `slow`：跳过慢速测试：`pytest -m "not slow"`
- `integration`：集成测试
- `gpu`：需要 GPU 的测试

**测试目录结构**

测试按职责组织；以仓库当前目录为准，新增测试优先放入对应层级：

```text
tests/
├── api/                 # API 路由与接口行为
└── unit/                # 领域、核心逻辑、Agent、CLI 等单元测试
```

当前已有 `api/` 和 `unit/` 测试；不要依据文档假设测试目录为空。

## 提交前检查清单

根据变更范围执行以下检查：

- [ ] `black --check src/ tests/`
- [ ] `ruff check src/ tests/`
- [ ] `mypy src/penclip`
- [ ] `pytest`
- [ ] `pre-commit run --all-files`

`pytest` 已由 `pyproject.toml` 配置覆盖率报告；无需在文档中重复拼接覆盖率参数。

## 项目配置文件清单

| 文件                        | 作用                   |
| :-------------------------- | :--------------------- |
| `pyproject.toml`            | 统一配置中心           |
| `.pre-commit-config.yaml`   | Git 钩子配置           |
| `.env.example`              | 环境变量模板           |
| `.gitignore`                | Git 忽略规则           |

## 常见问题

**Q: ruff 报 import 顺序错误怎么办？**
```bash
ruff check --fix src/  # 自动修复导入顺序
```

**Q: black 与 ruff 冲突？**
不会。E501 已从 ruff 中排除，行长度由 black 统一管理。

**Q: 如何只检查变更的文件？**
```bash
git diff --name-only HEAD | grep '\.py$' | xargs black
git diff --name-only HEAD | grep '\.py$' | xargs ruff check
```

**Q: 如何忽略某个特定的 lint 规则？**
在代码行末添加 `# noqa: RULE_CODE`，或在 `pyproject.toml` 的 `tool.ruff.ignore` 列表中添加。
