# aioclaw

[![Python Version](https://img.shields.io/badge/python-%3E%3D3.11-blue)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-0.2.0-green)]()

基于 `aioverse` 构建的异步 AI Agent 框架。内置 **AI 自动调用循环**、**技能 (Skill) 系统**、**上下文压缩** 与 **灵活的密钥管理**。核心数据基于 `Pydantic v2`，类型安全，IDE 友好。

> 设计哲学：**协议驱动、配置优先、易于扩展**

---

## ✨ 特性

- **纯异步架构** — `aiohttp` + `asyncio`，高并发无压力
- **自动工具循环** — `AssistantCaller` 自动处理 AI 调用与工具执行的循环，无需手动管理 `tool_calls`
- **技能系统** — 从 Markdown / JSON 文件加载技能，运行时动态匹配注入
- **上下文压缩** — 自动检测 Token 溢出并触发裁剪
- **智能密钥管理** — `KeysManager` 支持密钥缓存、可用性状态追踪，异常时自动切换
- **配置驱动** — 一份 JSON 配置搞定模型、路径、技能与运行时参数
- **丰富内置工具** — 文件读写、目录扫描、网络请求、代码运行、Shell 命令、技能查询等开箱即用
- **可扩展协议** — 模型管理、工具管理、技能管理、上下文压缩均可轻松替换实现

---

## 📦 安装

```bash
pip install aioclaw
```

### 依赖

| 包名 | 版本 |
|------|------|
| Python | >= 3.11 |
| aioverse | — |
| pydantic | >= 2.13.4 |
| orjson | >= 3.11.9 |
| aiofiles | >= 25.1.0 |
| python-frontmatter | — |
| trafilatura | >= 2.0.0 |
| fake-useragent | >= 2.2.0 |
| asyncstdlib | >= 3.14.0 |
| httpx | — |

---

## 🚀 快速开始

### 1. 配置文件

创建 `claw_config.json`：

```json
{
  "models_config": [
    {
      "model_name": "gpt-4o",
      "model_alias": "gpt4",
      "api_url": "https://api.openai.com/v1/chat/completions",
      "model_keys": ["sk-your-key"],
      "token_limit": 8000
    }
  ],
  "paths_config": [
    {
      "name": "workspace",
      "description": "工作目录",
      "path": "./workspace",
      "type": "dir"
    }
  ],
  "skills_config": {
    "path": "./skills"
  },
  "assistant_runtime_config": {
    "max_round": 50,
    "timeout": 300
  }
}
```

### 2. 代码启动

```python
import asyncio
import aiohttp
from aioclaw.models.claw_config import ClawConfig
from aioclaw.models.assistant_prompt import AssistantPrompt
from aioclaw.managers import ModelsManager, SkillsManager, ToolsManager
from aioclaw.core import AssistantCaller, ContextCompresser
from aioclaw.tools import (
    SkillOperationTools, FileOperationTools,
    NetworkOperationTools, CodeOperationTools
)
from aioclaw.utils.syntax_sugar import chain_tools_by_instance

async def main():
    claw_config = ClawConfig.from_file("claw_config.json")

    skills_manager = SkillsManager(claw_config.skills_config._skills)
    models_manager = ModelsManager(claw_config.models_config)
    tools_manager = ToolsManager()
    context_presser = ContextCompresser()
    assistant_prompt = AssistantPrompt()

    # 工具集聚合
    tool_set = chain_tools_by_instance(
        SkillOperationTools(skills_manager_instance=skills_manager, assistant_prompt=assistant_prompt),
        FileOperationTools(),
        NetworkOperationTools(),
        CodeOperationTools()
    )
    tool_set.register(tools_manager)

    async with aiohttp.ClientSession() as session:
        assistant_caller = AssistantCaller(
            tool_set=tool_set,
            tools_manager=tools_manager,
            session=session,
            models_manager=models_manager,
            assistant_prompt=assistant_prompt,
            context_presser=context_presser
        )

        # 选择模型
        assistant_caller.change_model(model_alias="gpt4")

        # 创建上下文并使用
        from aioverse.managers import ContextManager
        from aioverse.base_models.contexts import Context

        ctx = ContextManager()
        ctx.add_context(Context(role="user", content="你好！"))

        runtime = AssistantRuntime()
        async for output in assistant_caller.async_assistant_generator(
            context_manager=ctx,
            assistant_runtime=runtime
        ):
            if output.content:
                print(output.content)

asyncio.run(main())
```

---

## 📂 项目结构（v0.2.0）

```
aioclaw/
├── __init__.py
│
├── core/                          # 核心逻辑
│   ├── assistant_caller.py        # AI 自动调用循环（含密钥管理）
│   └── context_compresser.py      # 上下文压缩器
│
├── managers/                      # 管理器
│   ├── models_manager.py          # 模型配置查找
│   ├── tools_manager.py           # 工具注册与执行中心
│   ├── skills_manager.py          # 技能管理器（O(1) 哈希查找）
│   └── keys_manager.py            # 密钥管理器（缓存 + 可用性追踪）
│
├── tools/                         # 内置工具集
│   ├── file_operation_tools.py    # 文件读写操作
│   ├── network_operation_tools.py # HTTP 请求 + 内容提取
│   ├── code_operation_tools.py    # Python / Shell 执行
│   ├── skill_operation_tools.py   # 技能查找与学习
│   ├── system_operation_tools.py  # 系统操作工具
│   └── _final_tools.py            # 工具集聚合器
│
├── models/                        # 数据模型
│   ├── assistant_prompt.py        # 系统提示词 + 角色人设 + 技能缓存
│   ├── assistant_output.py        # AI 输出封装
│   ├── context_compress_result.py # 压缩结果
│   ├── skill.py                   # 技能模型（Markdown/YAML Frontmatter）
│   │
│   ├── config_models/             # 配置模型体系
│   │   ├── claw_config.py         # ClawConfig 完整配置
│   │   ├── base_config.py         # 基础配置
│   │   ├── path_config.py         # 路径配置
│   │   ├── skills_directory_config.py  # 技能目录配置
│   │   └── assistant_runtime_config.py # 运行时配置
│   │
│   └── runtime_models/            # 运行时模型
│       ├── assistant_runtime.py   # 运行时状态
│       └── tool_runtime.py        # 工具运行时状态
│
├── protocols/                     # 协议接口（面向接口编程）
│   ├── models_manager_protocol.py
│   ├── tools_manager_protocol.py
│   ├── skills_manager_protocol.py
│   ├── context_compress_protocol.py
│   └── tool_set_protocol.py
│
├── enums/                         # 枚举定义
│   ├── execute_status.py          # 执行状态枚举
│   └── file_types.py              # 文件类型枚举
│
├── errors/                        # 异常体系
│   ├── base_claw_error.py         # 基础异常
│   └── assistant_errors/          # AI Agent 异常集合
│
└── utils/                         # 工具函数
    ├── syntax_sugar.py            # 工具集语法糖聚合
    └── event_waiter.py            # 异步事件等待（带超时）
```

---

## 📚 API 参考

### AssistantCaller

AI 自动调用循环的核心。自动处理：调用 AI → 解析响应 → 执行工具 → 继续循环。

```python
class AssistantCaller:
    def __init__(
        self,
        models_manager  : ModelsManagerProtocol,
        tool_set        : ToolSetProtocol,
        tools_manager   : ToolsManagerProtocol,
        session         : aiohttp.ClientSession,
        context_presser : Optional[ContextCompressProtocol] = None,
        assistant_prompt: Optional[AssistantPrompt] = None,
        async_log       : Optional[LogProtocol] = None
    ): ...

    async def async_assistant_generator(
        self,
        context_manager    : ContextManager,
        assistant_runtime  : AssistantRuntime
    ) -> AsyncGenerator[AssistantOutput]: ...

    def change_model(self, **kwargs) -> Tuple[bool, ModelConfig | None]: ...
```

**变更说明：** `AssistantCaller` 内部管理 `KeysManager`，在 `change_model()` 时自动初始化。每次调用 AI 时通过 `keys_manager.get_available_key()` 获取可用密钥，支持缓存 O(1) 返回。

**调用流程：**

```
async_assistant_generator()
    ↓
更新提示词 → 压缩上下文（溢出时） → 获取可用密钥 → 调用 AI
    ↓
finish_reason == "tool_calls"?
    ├── 是 → 执行工具 → 添加上下文 → 继续循环
    └── 否 → yield AssistantOutput → 结束
```

### AssistantRuntime

运行时状态配置与追踪：

```python
class AssistantRuntime(BaseModel):
    timeout         : int = 300     # 单次 AI 调用超时
    max_rounds      : int = 50      # 最大总循环轮数
    current_rounds  : int = 0       # 当前轮数
    tool_calling_rounds: int = 0    # 工具调用轮数
    last_response_type: Optional[str] = None  # 上次返回类型
```

### AssistantOutput

AI 输出的标准化封装：

```python
class AssistantOutput(BaseModel):
    response_type       : str               # "stop" / "tool_calls"
    content             : Optional[str]     # 文本内容
    reasoning_content   : Optional[str]     # 推理内容（支持思考的模型）
```

### ContextCompresser

上下文压缩器。当 token 超出模型限制时自动裁剪最早上下文：

```python
class ContextCompresser:
    async def compress(
        self,
        context_manager: ContextManager,
        model_config: ModelConfig
    ) -> ContextCompressResult: ...
```

`ContextCompressResult` 包含：
- `is_out` — 是否溢出
- `is_compressed` — 是否已压缩

---

## 🔑 密钥管理 — KeysManager

全新的密钥管理器，支持缓存与可用性状态追踪。

```python
from aioclaw.managers import KeysManager
from aioverse.base_models import AssistantKey

keys = [
    AssistantKey(key="sk-1"),
    AssistantKey(key="sk-2", is_enable=False),  # 可禁用
]

km = KeysManager(keys)

# 获取可用密钥（优先从缓存返回，O(1)）
key = km.get_available_key()

# 缓存管理
km.cache_key(key)    # 缓存特定密钥
km.uncache_key()     # 清除缓存

# 状态管理
key.set_unavailable()  # 标记为不可用（如 API 返回 429）
key.set_available()    # 重新标记为可用
```

| 方法 | 说明 |
|------|------|
| `get_available_key()` | 获取可用密钥（先查缓存，再遍历 keys） |
| `cache_key(key)` | 缓存一个密钥 |
| `uncache_key()` | 清除缓存 |
| `_is_available_key(key)` | 判断密钥是否启用且可用 |

---

## 📋 管理器

### ModelsManager

模型配置查找：

```python
class ModelsManager:
    def find_model(
        self,
        model_name : Optional[str] = None,
        model_alias: Optional[str] = None,
        api_url    : Optional[str] = None
    ) -> ModelConfig | None: ...
```

### SkillsManager

技能管理器。从 Markdown / JSON 文件加载技能，支持 O(1) 哈希表查找：

```python
class SkillsManager:
    def find(self, keywords: str) -> List[Skill]: ...
    def add(self, skill: Skill): ...
    def remove(self, skill: Skill): ...
    def get_by_name(self, skill_name: str) -> Skill | None: ...
```

### ToolsManager

工具注册与执行中心。支持安全执行，不存在的工具返回友好提示而非抛异常：

```python
class ToolsManager:
    def register(self, func: callable, schema: Tool): ...
    async def execute_tool(self, tool_calling: ToolCalling) -> ToolOutput: ...
    def to_list(self) -> List[Dict[str, Any]]: ...
```

**安全机制：**
- 自动适配同步/异步函数（`func2coro`）
- 统一超时控制（`safe_execute_tool`，默认 30s）
- 错误捕获返回字符串，不会中断流程
- 不存在的工具返回 `"无法调用不存在的工具: {tool_name}"`

---

## 🔧 内置工具清单

| 工具名 | 说明 | 所属工具集 |
|--------|------|-----------|
| `read_file` | 完整读取文件内容 | FileOperationTools |
| `read_file_lines` | 按行读取文件 | FileOperationTools |
| `write_file` | 写入/覆盖/追加文件 | FileOperationTools |
| `change_file_line` | 修改文件指定行 | FileOperationTools |
| `copy_full_file` | 复制完整文件 | FileOperationTools |
| `delete_file` | 删除文件 | FileOperationTools |
| `scan_directory` | 扫描目录内容 | FileOperationTools |
| `find_in_file` | 在文件中搜索关键词 | FileOperationTools |
| `create_directory` | 创建目录（含父目录） | FileOperationTools |
| `fetch_url` | 异步 HTTP 请求 + 内容提取 | NetworkOperationTools |
| `python_runner` | 运行 Python 代码（支持超时、输出裁剪） | CodeOperationTools |
| `bash_runner` | 运行 Shell 指令（支持管道、工作目录、超时） | CodeOperationTools |
| `find_skills` | 搜索技能 | SkillOperationTools |
| `read_skill` | 读取/学习技能 | SkillOperationTools |

---

## 🔌 工具系统

### ToolSetProtocol

工具集协议。将相关工具分组，统一注册。

```python
class MyTools(ToolSetProtocol):
    def register(self, tools_manager: ToolsManagerProtocol):
        super().register(tools_manager)
        tools_manager.register(self.hello, hello_schema)

    def hello(self, name: str) -> str:
        return f"Hello, {name}!"
```

### 工具聚合

两种方式合并多个工具集：

```python
# 方式一：实例聚合（推荐）
from aioclaw.utils.syntax_sugar import chain_tools_by_instance

tool_set = chain_tools_by_instance(
    FileOperationTools(),
    NetworkOperationTools(),
    CodeOperationTools()
)
tool_set.register(tools_manager)

# 方式二：类聚合（Mixin）
from aioclaw.utils.syntax_sugar import chain_tools_by_class

FinalTools = chain_tools_by_class(FileOperationTools, NetworkOperationTools)
tool_set = FinalTools()
tool_set.register(tools_manager)
```

### ToolRuntime

单个工具的运行时状态跟踪（用于异步并发执行场景）。

```python
class ToolRuntime(BaseModel):
    tool_id         : str
    tool_name       : str
    tool_func       : Callable
    tool_arguments  : Dict[str, Any]
    tool_response   : str
    execute_status  : ExecuteStatus  # Pending / Finish / Hanging / Error
```

---

## 📋 技能 (Skill)

以 Markdown 格式编写的提示词片段，支持 YAML Frontmatter：

```markdown
---
name: 代码审查
description: 帮助用户审查代码质量
version: "1.0.0"
---

# 代码审查指南
1. 检查语法错误
2. 检查逻辑漏洞
3. 提供优化建议
```

```python
skills_manager = SkillsManager(skills_list)
found = skills_manager.find("代码 审查")
skill = skills_manager.get_by_name("代码审查")
```

---

## 🛠️ 工具函数

### event_waiter

异步事件等待，带超时控制：

```python
from aioclaw.utils.event_waiter import async_event_waiter

result = await async_event_waiter(some_coro(), timeout=30)
# 超时返回 None，正常返回 coro 结果
```

---

## ⚙️ 配置模型

### ClawConfig

完整的 JSON 配置结构：

```python
class ClawConfig(BaseModel):
    models_config           : List[ModelConfig]
    paths_config            : List[PathConfig]
    skills_config           : SkillsConfig
    assistant_runtime_config: AssistantRuntimeConfig

    @classmethod
    def from_file(cls, path: str) -> "ClawConfig": ...
```

| 配置段 | 说明 |
|--------|------|
| `models_config` | AI 模型列表（名称、地址、密钥、Token 限制） |
| `paths_config` | 路径配置（自动读取文件内容或创建目录） |
| `skills_config` | 技能目录路径（自动遍历加载 `.md` 文件） |
| `assistant_runtime_config` | 运行时配置（最大轮数、超时） |

### AssistantPrompt

系统提示词封装，包含 system_prompt、role_prompt、learned_skills 和自定义 metadata：

```python
class AssistantPrompt(BaseModel):
    system_prompt   : str = default_system_prompt
    role_prompt     : str = ""
    learned_skills  : Dict[str, str] = {}
    metadata        : Dict[str, Any] = {}

    def to_json(self) -> str: ...
    def add_metadata(self, key: str, value: Any) -> "AssistantPrompt": ...
```

---

## ❌ 错误处理

| 异常 | 说明 |
|------|------|
| `ClawError` | 所有异常的基类（位于 `errors.base_claw_error`） |
| `AssistantError` | AI Agent 相关异常的基类 |
| `ClientNotReady` | 客户端未初始化（`change_model` 未调用） |
| `ModelConfigNotFound` | 未找到匹配的模型配置 |
| `AssistantCallError` | AI 调用过程中的一般错误 |
| `MaxRoundLimit` | 超出最大循环轮数限制 |
| `UnknownResponseType` | AI 返回了未知的 `finish_reason` |

---

## 📋 枚举类型

| 枚举 | 说明 | 所在文件 |
|------|------|---------|
| `ExecuteStatus` | 工具执行状态（Pending / Finish / Hanging / Error） | `enums/execute_status.py` |
| `FileType` | 文件类型分类 | `enums/file_types.py` |

---

## 📋 数据模型一览

| 模块路径 | 模型 | 说明 |
|----------|------|------|
| `models.assistant_prompt` | `AssistantPrompt` | 系统提示词 + 人设 + 技能缓存 |
| `models.runtime_models.assistant_runtime` | `AssistantRuntime` | 运行时状态 |
| `models.assistant_output` | `AssistantOutput` | AI 输出封装 |
| `models.context_compress_result` | `ContextCompressResult` | 压缩结果 |
| `models.skill` | `Skill` | 技能（Markdown/Frontmatter） |
| `models.runtime_models.tool_runtime` | `ToolRuntime` | 工具运行时状态 |
| `models.config_models.claw_config` | `ClawConfig` | 完整配置 |
| `models.config_models.base_config` | `BaseConfig` | 基础配置 |
| `models.config_models.path_config` | `PathConfig` | 路径配置 |
| `models.config_models.skills_directory_config` | `SkillsDirectoryConfig` | 技能目录配置 |
| `models.config_models.assistant_runtime_config` | `AssistantRuntimeConfig` | 运行时配置 |
| `managers.keys_manager` | `KeysManager` | 密钥管理器 |
| `managers.models_manager` | `ModelsManager` | 模型管理器 |
| `managers.skills_manager` | `SkillsManager` | 技能管理器 |
| `managers.tools_manager` | `ToolsManager` | 工具管理器 |

---

## 📄 许可证

MIT License
