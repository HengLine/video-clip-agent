---
name: validation
description: PenClip code quality and validation — pre-commit hooks, ruff, black, mypy, pytest. Use when running checks, fixing lint errors, or setting up quality gates.
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
pytest tests/test_video_metadata.py -v

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

**测试目录结构**（按 DDD 分层，规划自 `docs/视频混剪智能体-设计原则.md`）：
```
tests/
├── unit/
│   ├── core/        # hub / orchestration / state / event
│   ├── agents/      # BaseAgent + 各 Agent
│   ├── domain/      # entities / value_objects / repositories
│   └── services/
├── integration/
├── e2e/
└── fixtures/
```

> 注意：当前 `tests/` 目录为空，测试用例是 V0.2 待办（见 `docs/AI开发导向-项目总览.md` §9）。新增测试请按上述分层组织。

## CI/CD 检查清单

每次提交前应通过：

- [ ] `black --check src/ tests/` 通过
- [ ] `ruff check src/ tests/` 无错误
- [ ] `mypy src/penclip` 无新增错误
- [ ] `pytest` 全部通过
- [ ] `pre-commit run --all-files` 通过

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
