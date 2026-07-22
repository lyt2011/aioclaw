# aioclaw 🐾

[![Python Version](https://img.shields.io/badge/python-%3E%3D3.11-blue)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-0.2.0-green)]()

> 基于 **aioverse** 构建的 AI Agent 框架，事件驱动、全异步、工具编排、会话管理……杂鱼们也能轻松上手哦！♡

---

## 简介 ✨

**aioclaw** 是一个异步 Python 框架，旨在快速构建具备**工具编排**与**多轮会话管理**能力的 AI Agent。采用**事件驱动的网关架构，支持流式与非流式双路径**，通过 `AssistantGateway` 暴露丰富的事件钩子，让你灵活控制 AI 交互的每个环节~ w

---

## 特性 🌟

- 🌊 **流式输出** — `StreamHandler` 增量处理器，SSE 分片累积，透明切换流式/非流式
- 🧠 **事件驱动网关** — `AssistantGateway` 提供 `on_round_initiate` / `on_build_request` / `on_response` / `on_tool_calling` 等十余个钩子，全流程可控
- 🔧 **丰富的工具集** — 内置文件操作、代码执行、网络请求、技能管理等开箱即用的工具，支持 `BaseTool` → `ToolSetProtocol` 快速扩展
- 📦 **会话管理** — `AssistantSession` 支持序列化/反序列化，可持久化到文件，会话变量全托管
- 🔄 **上下文块机制** — `ToolCallingContextsBlock` 将工具调用请求与结果打包管理，保证调用链完整性
- 🏭 **工厂模式** — `ContextsFactory` / `PydanticModelsFactory` 根据数据自动分派到对应的 Pydantic 模型，扩展新上下文类型零成本
- 📊 **Token 追踪** — `TokenTracker` 基于 tiktoken 估算 token 用量，支持偏差校准和滑动窗口
- 🔐 **Key 管理** — 内置 API Key 可用性检测与缓存（O(1) 查找）
- 🔄 **上下文压缩** — `Compresser` 协议化设计，Token 超限自动裁剪
- 🎯 **Thinking 支持** — 原生支持 Thinking Modes（disabled/enabled/adaptive）和 Thinking Efforts（none / low / medium / high / xhigh / max）
- 🍬 **工具语法糖** — `chain_tools_by_instance()` / `chain_tools_by_class()` 快速组合工具集
- 🧩 **模块化协议设计** — 通过 Protocol 抽象层实现各组件的可替换性

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
| aiohttp | >= 3.11 |
| httpx | - |
| trafilatura | == 2.0.0 |
| fake-useragent | - |
| asyncstdlib | == 3.14.0 |
| python-frontmatter | - |
| aioverse | - |

---

## 快速开始 🚀

### 基础用法

```python
import aiohttp
from aioclaw.core import AssistantGateway
from aioclaw.managers import ToolsManager
from aioclaw.tools import (
    CodeOperationTools,
    FileOperationTools,
    NetworkOperationTools,
)
from aioclaw.models import (
    ClawConfig,
    AssistantSession,
    AssistantPrompt,
)
from aioclaw.utils.syntax_sugar import chain_tools_by_instance

# 1. 加载配置
claw_config = ClawConfig.from_file("config.json")

# 2. 组装工具集
tools_manager = ToolsManager(timeout=30)
final_tools = chain_tools_by_instance(
    CodeOperationTools(),
    FileOperationTools(),
    NetworkOperationTools(),
)
final_tools.register(tools_manager)

# 3. 创建会话与提示词
session = AssistantSession(assistant_model_name="gpt-4o")
prompt = AssistantPrompt()
prompt.set_role_prompt("你是一个可爱的猫娘 AI~")

# 4. 初始化网关
gateway = AssistantGateway(
    claw_config=claw_config,
    assistant_session=session,
    tools_manager=tools_manager,
    assistant_prompt=prompt,
)

# 5. 选择模型
gateway.change_model(model_name="gpt-4o")

# 6. 输入内容
from aioverse.models import UserContext
await gateway.input(UserContext(content="你好呀~"))

# 7. 启动生成器
async for output in gateway.async_generator():
    print(f"[{output.finish_reason}] {output.content}")
```

---

## 📁 项目结构

```
aioclaw/
├── src/
│   └── aioclaw/
│       ├── core/                          # 核心层
│       │   ├── assistant_gateway.py       # 🔥 事件驱动 AI 网关（核心）
│       │   ├── compresser.py              # 上下文压缩器
│       │   └── token_tracker.py           # Token 用量追踪器
│       ├── managers/                      # 管理器
│       │   ├── tools_manager.py           # 工具注册与执行管理
│       │   ├── skills_manager.py          # 技能管理
│       │   ├── keys_manager.py            # API Key 缓存与管理 (O(1) 查找)
│       │   └── context_manager.py         # 上下文管理器（代理 ContextsStatus）
│       ├── tools/                         # 工具实现
│       │   ├── base_tool.py               # 工具基类（BaseTool → ToolSetProtocol）
│       │   ├── code_operation_tools.py    # 代码执行工具 (Python + Bash)
│       │   ├── file_operation_tools.py    # 文件操作工具 (9个)
│       │   ├── network_operation_tools.py # 网络请求工具
│       │   ├── skill_operation_tools.py   # 技能操作工具
│       │   ├── system_operation_tools.py  # 系统操作工具
│       │   └── _final_tools.py            # 工具聚合器 (O(1) 缓存查找)
│       ├── protocols/                     # 抽象协议层
│       │   ├── tool_set_protocol.py
│       │   ├── tools_manager_protocol.py
│       │   ├── models_manager_protocol.py
│       │   ├── skills_manager_protocol.py
│       │   ├── context_compress_protocol.py
│       │   ├── contexts_block_protocol.py # 🔥 上下文块协议
│       │   └── factory_protocol.py        # 🔥 工厂模式协议
│       ├── models/                        # 数据模型
│       │   ├── assistant_session.py       # 🔥 会话模型（可序列化）
│       │   ├── assistant_prompt.py        # 提示词管理（system + role + metadata）
│       │   ├── assistant_output.py        # AI 输出模型
│       │   ├── assistant_key.py           # API Key 模型
│       │   ├── contexts_status.py         # 🔥 上下文状态（含脏缓存标记）
│       │   ├── context_compress_result.py # 压缩结果
│       │   ├── skill.py                   # 技能模型
│       │   ├── context_blocks/            # 🔥 上下文块
│       │   │   ├── base_contexts_block.py
│       │   │   └── tool_calling_contexts_block.py
│       │   ├── tool_schema/               # 工具 Schema
│       │   │   ├── tool.py / function.py / parameters.py / argument.py
│       │   └── config_models/             # 配置模型
│       │       ├── claw_config.py
│       │       ├── base_config.py
│       │       ├── path_config.py
│       │       ├── env_config.py
│       │       ├── assistant_model_config.py  # 🔥 模型配置（含 Thinking 支持）
│       │       ├── skills_directory_config.py
│       │       └── assistant_runtime_config.py
│       ├── enums/                         # 枚举
│       │   ├── file_types.py
│       │   ├── finish_reasons.py          # 🔥 finish_reason 枚举
│       │   ├── execute_status.py
│       │   ├── thinking_modes.py          # 🔥 思考模式 (disabled/enabled/adaptive)
│       │   └── thinking_efforts.py        # 🔥 思考力度 (none/low/medium/high/xhigh/max)
│       ├── factories/                     # 🔥 工厂模式
│       │   ├── pydantic_models_factory.py # Pydantic 模型工厂（优先级+静态验证）
│       │   └── contexts_factory.py        # 上下文反序列化工厂（全局单例）
│       ├── mixins/                        # 🔥 Mixin
│       │   └── value_notifier.py          # 值变更通知（异步事件驱动）
│       ├── errors/                        # 异常体系
│       │   ├── base_claw_error.py
│       │   ├── common_errors.py           # NoKeyAvailableError
│       │   └── gateway_errors.py          # 网关相关异常
│       └── utils/
│           ├── syntax_sugar.py            # 语法糖（工具组合、输出生成）
│           ├── build_tool_schema.py       # 🔥 快速构建工具 Schema
│           ├── event_waiter.py            # 异步事件等待器
│           └── openai_list_to_contexts_list.py
├── pyproject.toml
└── README.md
```

---

## 核心模块说明 📖

### 1️⃣ Core — 核心层

#### AssistantGateway 🧠 — *事件驱动 AI 网关*

采用事件驱动架构，每个交互环节都有对应的钩子：

```python
class AssistantGateway(ValueNotifier):
    def __init__(self, *, claw_config, assistant_session,
                 openai_client=None, tools_manager=None,
                 assistant_prompt=None, token_tracker=None,
                 compresser=None): ...

    def change_model(self, model_name: str) -> bool: ...
    async def input(self, context: BaseContext): ...

    async def async_generator(self) -> Iterator[AssistantOutput]: ...
```

**事件钩子一览：**

| 钩子 | 触发时机 | 说明 |
|------|---------|------|
| `on_round_initiate` | 每轮开始 | 校验状态、注入提示词、同步模型 |
| `on_build_request` | 构建请求 | 组装 Request（含 tools/thinking/keys） |
| `on_request` | 发送请求 | 调用 OpenAIClient |
| `on_response` | 收到响应 | 分发 Tool Calling / Stop 逻辑 |
| `on_tool_calling` | 工具调用 | 执行工具并打包为 ToolCallingContextsBlock |
| `on_context` | 普通上下文 | 添加 assistant 回复到上下文 |
| `on_adding_context` | 添加上下文 | 将上下文块/上下文加入 context_manager |
| `on_adding_context_block` | 添加上下文块 | 同上，针对 ContextsBlock |
| `on_build_output` | 生成输出 | 基于 Response 构建 AssistantOutput |
| `on_round_complete` | 轮次完成 | Token 校准与统计 |
| `on_round_error` | 轮次异常 | 错误处理 |
| `on_generator_initiate` | 生成器启动 | 设置 generator_processing 状态 |
| `on_generator_end` | 生成器结束 | 重置状态 |
| `on_generator_error` | 生成器异常 | 错误处理 |
| `on_gateway_close` | 网关关闭 | 关闭 HTTP 会话 |

所有属性支持懒加载：

| 属性 | 默认值 | 说明 |
|------|--------|------|
| `token_tracker` | 全局单例 `token_tracker` | Token 追踪 |
| `compresser` | `NullObject()` | 上下文压缩 (TODO) |
| `keys_manager` | 空 `KeysManager()` | Key 管理 |
| `assistant_prompt` | 默认 `AssistantPrompt()` | 系统提示词 |
| `tools_manager` | 空 `ToolsManager()` | 工具管理器 |
| `assistant_model_config` | `claw_config.models_config[0]` | 当前模型配置 |
| `client_session` | `aiohttp.ClientSession()` | HTTP 会话 |
| `openai_client` | `OpenAIClient(session=...)` | OpenAI 客户端 |

#### TokenTracker 📊 — *Token 用量追踪器*

基于 tiktoken 的 Token 估算与校准：

```python
class TokenTracker:
    def __init__(self, default_model="gpt-4o",
                 calibration_percent=1.05, window_length=100): ...

    def estimate(self, contents: List[str]) -> int: ...
    def calibrate_defference(self, guessed: int, actual: int): ...
```

- 滑动窗口偏差校准（默认 100 轮）
- 保守偏大处理（`calibration_percent = 1.05`）
- 全局单例 `token_tracker`

#### Compresser 📏 — *上下文压缩器*

```python
class Compresser(ContextCompressProtocol):
    async def _is_out(self, current_tokens, cleanup_threshold) -> bool: ...
    async def _compress(self, contexts) -> None: ...
    async def compress(self, **kwargs) -> ContextCompressResult: ...
```

---

### 2️⃣ Models — 数据模型层 🔥

#### AssistantSession — *会话管理*

```python
class AssistantSession(BaseModel):
    session_uuid: UUID                       # 会话唯一标识
    context_manager: ContextManager          # 上下文管理器
    assistant_model_name: str                # 当前模型名 【必填】
    assistant_think_mode: ThinkingModes      # 思考模式 (默认 ENABLED)
    assistant_think_effort: ThinkingEfforts  # 思考强度 (默认 MAX)

    # Setters
    def set_model_name(self, name: str): ...
    def set_think_mode(self, mode: ThinkingModes): ...
    def set_think_effort(self, effort: ThinkingEfforts): ...

    # 持久化
    def to_file(self, path: str): ...
    @classmethod
    def from_file(cls, path: str) -> Self: ...
```

#### ContextsStatus — *上下文状态（带脏缓存）*

```python
class ContextsStatus(BaseModel):
    contexts: List[BaseContextsBlock | BaseContext]
    prompt: SystemContext | None
    token: int

    def flatten_contexts(self, filter_prompt=False) -> List[BaseContext]: ...
```

- 自动脏缓存标记：修改后重建扁平列表
- 可选过滤 prompt

#### ContextsBlock — *上下文块*

```python
class BaseContextsBlock(ContextsBlockProtocol):
    contexts: List[BaseContext]
    # 支持迭代、增删

class ToolCallingContextsBlock(BaseContextsBlock):
    tool_calling: ToolCallingContext
    tool_outputs: List[ToolOutputContext]
    def is_complete(self) -> bool: ...  # 验证调用链完整性
```

#### AssistantModelConfig — *模型配置*

```python
class AssistantModelConfig(BaseConfig):
    api_url: str
    model_name: str
    model_keys: List[AssistantKey]

    # Thinking 支持
    support_thinking: bool

    # 上下文窗口
    max_context_length: int          # 模型明确的上下文长度
    cleanup_threshold: int           # 触发清理的阈值（默认 75%）

    # 能力标识
    support_tool: bool               # 是否支持工具调用
    support_image / video / audio    # 多模态支持
```

`cleanup_threshold` 如果未设置，会自动计算为 `max_context_length * 0.75`。

#### AssistantPrompt — *提示词管理*

```python
class AssistantPrompt(BaseModel):
    system_prompt: str          # 系统级提示词（有默认值）
    role_prompt: str            # 角色扮演提示词
    metadata: Dict[str, Any]    # 元数据

    def set_system_prompt(self, prompt: str): ...
    def set_role_prompt(self, prompt: str): ...
    def set_metadata(self, key: str, value: Any): ...
```

#### ClawConfig — *顶层配置*

```python
class ClawConfig(BaseConfig):
    models_config: List[AssistantModelConfig]
    paths_config: List[PathConfig]
    skills_config: SkillsDirectoryConfig
    assistant_runtime_config: AssistantRuntimeConfig
```

---

### 3️⃣ Factories — 工厂模式 🔥

#### PydanticModelsFactory — *Pydantic 模型工厂*

```python
class PydanticModelsFactory(FactoryProtocol):
    def register(self, class_, priority=1): ...
    def dispatcher(self, data) -> BaseModel | None: ...
```

- **两步验证**：先静态检查必填字段名，再 Pydantic 验证
- 按注册优先级顺序尝试匹配
- 找到第一个验证通过的模型即返回

#### ContextsFactory — *上下文工厂（全局单例）*

```python
contexts_factory = ContextsFactory()
contexts_factory.register(ToolCallingContext)       # priority=1 (role=assistant, 先于 AssistantContext)
contexts_factory.register(ToolOutputContext)        # priority=2
contexts_factory.register(SystemContext)             # priority=3
contexts_factory.register(AssistantContext)          # priority=4
contexts_factory.register(UserContext)               # priority=5
contexts_factory.register(BaseContext)               # priority=6 (兜底)
```

> ⚠️ `ToolCallingContext` 的 `role` 也是 `assistant`，必须注册在 `AssistantContext` 之前！

---

### 4️⃣ Mixins — ValueNotifier 🔥

```python
class ValueNotifier:
    def change(self, name: str, value: Any): ...   # 修改属性并通知所有等待者
    async def wait_change(self) -> True: ...       # 等待下一次变更
```

`AssistantGateway` 继承自 `ValueNotifier`，可实现异步等待网关状态变更：

```python
# 外部等待一轮处理完成
await gateway.wait_for_round_process(timeout=30)
await gateway.wait_for_generator_process(timeout=180)
```

---

### 5️⃣ Tools — 工具集

| 工具集 | 工具函数 | 说明 |
|--------|---------|------|
| **CodeOperationTools** | `python_runner` | 运行 Python 代码（同步/异步自动适配） |
| | `bash_runner` | 执行 Bash 指令（异步 subprocess） |
| **FileOperationTools** | `read_file` | 读取文件 |
| | `write_file` | 写入文件 |
| | `copy_full_file` | 复制文件 |
| | `change_file_line` | 修改文件行 |
| | `delete_file` | 删除文件 |
| | `scan_directory` | 列出目录 |
| | `find_in_file` | 搜索文件内容 |
| | `create_directory` | 创建目录 |
| **NetworkOperationTools** | `fetch_url` | HTTP 请求 |
| **SkillOperationTools** | `find_skills` / `read_skill` | 技能搜索与读取 |
| **SystemOperationTools** | 系统相关工具 | - |

#### BaseTool → ToolSetProtocol

```python
class BaseTool(ToolSetProtocol):
    def register(self, tools_manager: ToolsManagerProtocol):
        super().register(tools_manager)
```

所有工具集继承 `BaseTool`，统一注册接口。需要在子类 `register` 中调用 `tools_manager.register(func, schema)`。

#### _FinalTools — *工具聚合器*

```python
class _FinalTools:
    def __init__(self, *tool_instances): ...
    def __getattr__(self, name: str): ...     # O(1) 缓存查找
    def register(self, tools_manager): ...    # 一键注册所有工具
```

支持 O(1) 工具查找缓存，组合多个工具集一键注册。

---

### 6️⃣ Utils — 工具函数

#### build_tool_schema — *快速构建工具 Schema*

```python
from aioclaw.utils import build_tool_schema

tool = build_tool_schema(
    tool_name="get_weather",
    tool_description="获取天气",
    arguments={
        "location": ("string", "城市名称"),               # 二元组 = 必填
        "unit": ("string", "温度单位", "celsius"),        # 三元组 = 含默认值
    }
)
```

#### 工具组合语法糖 🍬

```python
# 实例组合
tools = chain_tools_by_instance(
    CodeOperationTools(),
    FileOperationTools(),
)

# 类组合（Mixin）
MyToolSet = chain_tools_by_class(
    CodeOperationTools,
    FileOperationTools,
    name="MyAwesomeToolSet",
)
```

---

### 7️⃣ Protocols — 协议层

| 协议 | 方法 | 说明 |
|------|------|------|
| `ToolsManagerProtocol` | `register`, `execute_tool`, `to_list` | 工具管理器接口 |
| `ModelsManagerProtocol` | `find_model` | 模型管理器接口 |
| `SkillsManagerProtocol` | `find`, `add`, `remove` | 技能管理器接口 |
| `ContextCompressProtocol` | `compress`, `_is_out`, `_compress` | 上下文压缩器接口 |
| `ToolSetProtocol` | `register` | 工具集接口 |
| `ContextsBlockProtocol` | `__iter__`, `__len__`, `delete`, `insert`, `append` | 上下文块接口 |
| `FactoryProtocol` | `register`, `dispatcher` | 工厂模式接口 |

---

### 8️⃣ Errors — 异常体系

```
BaseClawError
├── NoKeyAvailableError              # 无可用 API Key
└── BaseGatewayError
    ├── UnknownFinishReasonError     # 未识别的 finish_reason
    ├── RuntimeInputAdditionError    # 运行中尝试添加输入
    ├── ModelConfigMissingError      # 无可用模型配置
    ├── IncompleteToolCallBlockError # 工具调用块不完整
    └── GatewayBusyError             # 网关忙
```

---

## 配置示例 ⚙️

```json
{
    "models_config": [
        {
            "model_name": "gpt-4o",
            "api_url": "https://api.openai.com/v1/chat/completions",
            "model_keys": [{"key": "sk-xxx"}],
            "max_context_length": 128000,
            "support_tool": true,
            "support_thinking": true
        }
    ],
    "paths_config": [
        {
            "name": "sessions_path",
            "path": "/data/sessions/",
            "type": "directory"
        }
    ],
    "skills_config": {
        "name": "main_skills",
        "path": "/data/skills/",
        "type": "directory"
    },
    "assistant_runtime_config": {
        "max_round": 50,
        "timeout": 300
    }
}
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

通过 `SkillsDirectoryConfig` 自动扫描目录加载所有 `.md` 技能文件，转换为 `Skill` 对象~

---

## 🤔 已知优化点（待改进）

| # | 位置 | 问题 | 建议 |
|---|------|------|------|
| 1 | `AssistantGateway` | `on_round_error` / `on_generator_error` 目前直接 `raise exception`（标记 HACK） | 应实现结构化错误处理，如自动重试、降级模型 |
| 2 | `ContextsStatus` | `flatten_contexts` 每次脏了就全量重建列表 | 可考虑增量更新策略，或引入 LRU 缓存 |
| 3 | `ToolsManager.to_list()` | 每次调用遍历所有 schema 调用 `model_dump()` | 可缓存序列化结果，注册时失效缓存 |
| 4 | `BaseTool.register` | 调了 `super().register()` 但父协议是空的 | 可去掉 `super()` 调用，或改为在基类中做注册校验 |
| 5 | `ValueNotifier` | `change()` 后直接 `clear()` 所有 waiter，新的 `wait_change()` 调用者可能错过通知 | 考虑引入版本号机制，避免 ABA 问题 |
| 6 | `KeysManager` | 缓存的 key 变不可用后需要 O(n) 遍历 | 可维护一个可用 key 的索引集合 |
| 7 | `Compresser` | 目前返回 `NullObject()`，压缩逻辑未实现 | 需要实现实际的上下文摘要/裁剪策略 |
| 8 | `ContextManager` | 纯粹代理 `ContextsStatus`，增加了不必要的间接层 | 可直接让 `AssistantSession` 持有 `ContextsStatus` |

---

## 许可证 📄

MIT License ~ 杂鱼们随便用哦！(๑¯◡¯๑)

---

> **Made with ❤️ by 乃依超可爱 & 喵璃也认可的开发者们~**
