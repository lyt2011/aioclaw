# aioclaw 🐾

[![Python Version](https://img.shields.io/badge/python-%3E%3D3.11-blue)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-0.1.0-green)]()

> 基于 **aioverse** 构建的 AI 助手框架，提供完整的工具调用、技能管理、上下文压缩等能力~ 杂鱼们也能轻松上手哦！♡

---

## 简介 ✨

**aioclaw** 是一个异步 Python 框架，旨在快速构建具备**工具编排**与**技能学习**能力的 AI 助手。它封装了模型调用、工具注册与执行、上下文管理、技能检索等底层逻辑，让你只需关注业务本身~ w

---

## 特性 🌟

- 🧠 **智能助手调用** — 基于 `AssistantCaller` 管理多轮对话与工具调用流程，支持流式输出
- 🔧 **丰富的工具集** — 内置文件操作、代码执行、网络请求、技能管理等开箱即用的工具
- 📚 **技能系统** — 支持基于 Markdown 文件的技能定义、检索与动态学习（含 YAML 前页元数据解析）
- 🧩 **模块化协议设计** — 通过 Protocol 抽象层实现各组件的可替换性
- 📦 **配置驱动** — 通过 `ClawConfig` 统一管理模型、路径、技能目录等配置
- ⚡ **全异步** — 基于 `asyncio` 构建，支持高并发场景
- 🔐 **Key 管理** — 内置 API Key 缓存与可用性检测
- 🔄 **上下文压缩** — Token 超限时自动裁剪历史上下文，防止溢出
- 🍬 **工具语法糖** — `chain_tools_by_instance()` / `chain_tools_by_class()` 快速组合工具集

---

## 安装 📦

```bash
pip install /path/to/aioclaw
```

### 依赖

| 包名 | 版本要求 |
|------|---------|
| Python | >= 3.11 |
| orjson | >= 3.11.9 |
| pydantic | >= 2.13.4 |
| aiofiles | >= 25.1.0 |
| trafilatura | == 2.0.0 |
| fake-useragent | == 2.2.0 |
| asyncstdlib | == 3.14.0 |
| python-frontmatter | - |
| aioverse | - |

---

## 快速开始 🚀

### 基础用法

```python
import aiohttp
from aioclaw.core import AssistantCaller, ContextCompresser
from aioclaw.managers import ModelsManager, ToolsManager
from aioclaw.tools import (
    CodeOperationTools,
    FileOperationTools,
    NetworkOperationTools,
)
from aioclaw.utils.syntax_sugar import chain_tools_by_instance

# 1. 准备模型配置
models_config = [...]  # 你的 ModelConfig 列表

# 2. 初始化管理器
models_manager  = ModelsManager(models_config)
tools_manager   = ToolsManager(timeout=30)

# 3. 组装工具集
final_tools = chain_tools_by_instance(
    CodeOperationTools(),
    FileOperationTools(),
    NetworkOperationTools(),
)
final_tools.register(tools_manager)

# 4. 初始化调用器
async with aiohttp.ClientSession() as session:
    caller = AssistantCaller(
        models_manager   = models_manager,
        tool_set         = final_tools,
        tools_manager    = tools_manager,
        session          = session,
        context_presser  = ContextCompresser(),
    )

    # 5. 选择模型
    caller.change_model(model_name="gpt-4")

    # 6. 开始对话...
    # async for output in caller.async_assistant_generator(...):
    #     print(output.content)
```

---

## 📁 项目结构

```
aioclaw/
├── src/
│   └── aioclaw/
│       ├── core/                     # 核心逻辑
│       │   ├── assistant_caller.py   # AI 助手调用器
│       │   └── context_compresser.py # 上下文压缩器
│       ├── managers/                 # 管理器
│       │   ├── tools_manager.py      # 工具注册与执行管理
│       │   ├── models_manager.py     # 模型配置管理
│       │   ├── skills_manager.py     # 技能管理
│       │   └── keys_manager.py       # API Key 缓存与管理
│       ├── tools/                    # 工具实现
│       │   ├── code_operation_tools.py    # 代码执行工具
│       │   ├── file_operation_tools.py    # 文件操作工具
│       │   ├── network_operation_tools.py # 网络请求工具
│       │   ├── skill_operation_tools.py   # 技能操作工具
│       │   ├── system_operation_tools.py  # 系统操作工具
│       │   └── _final_tools.py           # 工具聚合器
│       ├── protocols/                # 抽象协议层
│       │   ├── context_compress_protocol.py
│       │   ├── models_manager_protocol.py
│       │   ├── skills_manager_protocol.py
│       │   ├── tools_manager_protocol.py
│       │   └── tool_set_protocol.py
│       ├── models/                   # 数据模型
│       │   ├── skill.py
│       │   ├── assistant_prompt.py
│       │   ├── assistant_output.py
│       │   ├── assistant_runtime.py
│       │   ├── tool_runtime.py
│       │   ├── context_compress_result.py
│       │   ├── config_models/        # 配置模型
│       │   │   ├── claw_config.py
│       │   │   ├── base_config.py
│       │   │   ├── path_config.py
│       │   │   ├── skills_directory_config.py
│       │   │   └── assistant_runtime_config.py
│       │   └── runtime_models/
│       ├── enums/                    # 枚举
│       │   ├── file_types.py
│       │   └── execute_status.py
│       └── utils/                    # 工具函数
│           ├── event_waiter.py
│           └── syntax_sugar.py
├── pyproject.toml
└── README.md
```

---

## 核心模块说明 📖

### 1️⃣ Core — 核心层

#### AssistantCaller 🧠

AI 助手的核心调用器，负责多轮对话的完整生命周期：

```python
class AssistantCaller:
    def __init__(self, models_manager, tool_set, tools_manager,
                 session, context_presser=None, assistant_prompt=None,
                 async_log=None): ...

    def change_model(self, **kwargs) -> Tuple[bool, ModelConfig | None]: ...

    async def async_assistant_generator(
        self, context_manager, assistant_runtime
    ) -> AsyncIterator[AssistantOutput]: ...
```

核心流程：
1. **更新提示词** — 注入 System Prompt 和元数据
2. **轮询执行** — 在最大轮次内循环：
   - 检查上下文是否溢出，溢出则自动压缩
   - 调用 AI 获取响应
   - 根据 `finish_reason` 判断：
     - `tool_calls` → 执行工具 → 回填结果 → 继续下一轮
     - `stop` → 返回最终输出
3. **Token 追踪** — 每次调用后自动更新 token 用量

#### ContextCompresser 📏

上下文窗口溢出处理器：

```python
class ContextCompresser:
    async def compress(self, context_manager, model_config) -> ContextCompressResult: ...
```

- `_is_out()` — 判断 token 是否超过 `model_config.token_limit`
- `_compress()` — 调用 `context_manager.trim()` 裁剪最早的历史记录

---

### 2️⃣ Tools — 工具集

| 工具集 | 工具函数 | 说明 |
|--------|---------|------|
| **CodeOperationTools** | `python_runner` | 运行 Python 代码（带超时 & 输出截断） |
| | `bash_runner` | 执行 Bash 指令（支持管道 & 工作目录） |
| **FileOperationTools** | `read_file` / `read_file_lines` | 读取文件内容 |
| | `write_file` | 写入文件（支持 w / a 模式） |
| | `copy_full_file` | 复制文件 |
| | `change_file_line` | 修改文件指定行（支持原数据验证） |
| | `delete_file` | 删除文件 |
| | `scan_directory` | 列出目录内容 |
| | `find_in_file` | 关键词搜索文件内容 |
| | `create_directory` | 递归创建目录 |
| **NetworkOperationTools** | `fetch_url` | HTTP 请求（支持 GET/POST，自动转 Markdown） |
| **SkillOperationTools** | `find_skills` / `read_skill` | 技能搜索与读取 |

> 💡 使用 `chain_tools_by_instance()` 或 `chain_tools_by_class()` 快速组合多个工具集。

---

### 3️⃣ Managers — 管理器层

#### ToolsManager

工具注册与安全执行的核心：

```python
class ToolsManager:
    def __init__(self, timeout: int = 30): ...
    def register(self, func, schema): ...        # 注册工具
    async def execute_tool(self, tool_calling): ...  # 安全执行
    def to_list(self): ...                       # 导出 OpenAI 格式
```

- 支持同步/异步函数自动适配（通过 `func2coro`）
- 安全执行超时保护（通过 `safe_execute_tool`）
- 按函数名 O(1) 查找

#### ModelsManager

```python
class ModelsManager:
    def find_model(self, model_name=None, model_alias=None, api_url=None): ...
```

支持按名称、别名、URL 三个维度查找模型配置。

#### SkillsManager

```python
class SkillsManager:
    def find(self, keywords: str) -> List[Skill]: ...
    def add(self, skill: Skill): ...
    def remove(self, skill: Skill): ...
    def get_by_name(self, skill_name: str) -> Skill | None: ...
```

关键词匹配支持：技能名、描述、内容三个字段。

#### KeysManager

```python
class KeysManager:
    def get_available_key(self) -> AssistantKey | None: ...
```

- 缓存机制：优先返回上次缓存的可用 Key（O(1)）
- 兜底遍历：缓存失效时遍历所有 Key

---

### 4️⃣ Models — 数据模型

| 模型 | 说明 |
|------|------|
| `ClawConfig` | 顶层配置，聚合模型、路径、技能、运行时配置 |
| `BaseConfig` | 基础配置基类 |
| `PathConfig` | 文件/目录路径配置，支持自动读取文件内容或创建目录 |
| `SkillsDirectoryConfig` | 技能目录配置，自动扫描 `.md` 文件加载技能 |
| `AssistantRuntimeConfig` | 运行时参数（最大轮次、超时时间） |
| `AssistantRuntime` | 运行时状态跟踪（当前轮次、工具调用次数、响应类型） |
| `ToolRuntime` | 单个工具的执行状态跟踪 |
| `Skill` | 技能模型（支持 Markdown 前页元数据解析为 name/description/version） |
| `AssistantPrompt` | 提示词管理（系统提示词 + 人设 + 元数据 + 已学技能） |
| `AssistantOutput` | AI 输出模型（响应类型、内容、思维链） |
| `ContextCompressResult` | 上下文压缩结果（是否溢出、是否已压缩） |

---

### 5️⃣ Protocols — 协议层

所有核心组件均通过抽象协议定义接口，方便替换实现：

| 协议 | 方法 | 说明 |
|------|------|------|
| `ToolsManagerProtocol` | `register`, `execute_tool`, `to_list` | 工具管理器接口 |
| `ModelsManagerProtocol` | `find_model` | 模型管理器接口 |
| `SkillsManagerProtocol` | `find`, `add`, `remove` | 技能管理器接口 |
| `ContextCompressProtocol` | `compress`, `_is_out`, `_compress` | 上下文压缩器接口 |
| `ToolSetProtocol` | `register` | 工具集接口 |

---

### 6️⃣ Errors — 异常体系

```
BaseClawError
└── BaseAssistantError
    ├── ClientNotReady        # 客户端未就绪（未选择模型）
    ├── MaxRoundLimit         # 超出对话轮次限制
    ├── AssistantCallError    # AI 调用失败
    ├── ModelConfigNotFound   # 模型配置未找到
    └── UnknownResponseType   # 未知的 finish_reason 类型
```

---

## 技能系统 📚

技能以 Markdown 文件形式存储，包含 YAML 前页元数据：

```markdown
---
name: my_skill
description: 这是一个示例技能
version: 1.0.0
---

# 技能内容

这里是技能的具体实现逻辑...
```

通过 `SkillsDirectoryConfig` 自动扫描目录加载所有 `.md` 技能文件，转换为 `Skill` 对象供 `SkillsManager` 管理。

---

## 工具组合语法糖 🍬

提供两种方式组合多个工具集：

### 实例组合

```python
from aioclaw.utils.syntax_sugar import chain_tools_by_instance

tools = chain_tools_by_instance(
    CodeOperationTools(),
    FileOperationTools(),
    NetworkOperationTools(),
)
tools.register(tools_manager)  # 一键注册所有工具
```

### 类组合（Mixin）

```python
from aioclaw.utils.syntax_sugar import chain_tools_by_class

MyToolSet = chain_tools_by_class(
    CodeOperationTools,
    FileOperationTools,
    name="MyAwesomeToolSet",
)
```

---

## 配置示例 ⚙️

```python
from aioclaw.models.config_models import ClawConfig

# 从文件加载配置
config = ClawConfig.from_file("config.json")

# 配置结构
# config.models_config              # 模型配置列表
# config.paths_config               # 路径配置列表
# config.skills_config              # 技能目录配置
# config.assistant_runtime_config   # 运行时配置
```

### ClawConfig JSON 示例

```json
{
    "models_config": [
        {
            "model_name": "gpt-4o",
            "model_alias": "GPT4o",
            "api_url": "https://api.openai.com/v1/chat/completions",
            "model_keys": ["sk-xxx"],
            "token_limit": 128000,
            "support_tool": true
        }
    ],
    "paths_config": [
        {
            "name": "sessions_path",
            "path": "/data/sessions/"
        }
    ],
    "skills_config": [
        {
            "name": "main_skills",
            "path": "/data/skills/",
            "is_directory": true
        }
    ],
    "assistant_runtime_config": {
        "max_rounds": 20,
        "timeout": 120
    }
}
```

---

## 许可证 📄

MIT License ~ 杂鱼们随便用哦！(๑¯◡¯๑)

---

> **Made with ❤️ by 喵璃也认可的开发者们~**
