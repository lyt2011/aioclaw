# aioclaw 🐾

> 一个基于 **aioverse** 构建的 AI 助手框架，提供完整的工具调用、技能管理、上下文压缩等能力~ 杂鱼们也能轻松上手哦！♡

---

## 简介 ✨

**aioclaw** 是一个异步 Python 框架，旨在快速构建具备**工具编排**与**技能学习**能力的 AI 助手。它封装了模型调用、工具注册与执行、上下文管理、技能检索等底层逻辑，让你只需关注业务本身~ w

---

## 特性 🌟

- 🧠 **智能助手调用** — 基于 `AssistantCaller` 管理多轮对话与工具调用流程
- 🔧 **丰富的工具集** — 内置文件操作、代码执行、网络请求、技能管理等开箱即用的工具
- 📚 **技能系统** — 支持基于 Markdown 文件的技能定义、检索与动态学习
- 🧩 **模块化协议设计** — 通过 Protocol 抽象层实现各组件的可替换性
- 📦 **配置驱动** — 通过 `ClawConfig` 统一管理模型、路径、技能目录等配置
- ⚡ **全异步** — 基于 `asyncio` 构建，支持高并发场景
- 🔐 **Key 管理** — 内置 API Key 缓存与可用性检测

---

## 安装 📦

```bash
pip install aioclaw
```

### 依赖

| 包名 | 版本要求 |
|------|---------|
| orjson | >=3.11.9 |
| pydantic | >=2.13.4 |
| aiofiles | >=25.1.0 |
| trafilatura | ==2.0.0 |
| fake-useragent | ==2.2.0 |
| asyncstdlib | ==3.14.0 |
| aioverse | - |
| python-frontmatter | - |

---

## 快速开始 🚀

### 基础用法

```python
import aiohttp
from aioclaw.core import AssistantCaller, ContextCompresser
from aioclaw.managers import ModelsManager, ToolsManager, SkillsManager
from aioclaw.tools import (
    CodeOperationTools,
    FileOperationTools,
    NetworkOperationTools,
    SkillOperationTools
)
from aioclaw.utils.syntax_sugar import chain_tools_by_instance

# 1. 准备模型配置
models_config = [...]  # 你的模型配置列表

# 2. 初始化管理器
models_manager  = ModelsManager(models_config)
tools_manager   = ToolsManager(timeout=30)
skills_manager  = SkillsManager(skills_list)

# 3. 组装工具集
final_tools = chain_tools_by_instance(
    CodeOperationTools(),
    FileOperationTools(),
    NetworkOperationTools(),
    SkillOperationTools(
        skills_manager_instance=skills_manager,
        assistant_prompt=assistant_prompt
    )
)
final_tools.register(tools_manager)

# 4. 初始化调用器
async with aiohttp.ClientSession() as session:
    caller = AssistantCaller(
        models_manager  = models_manager,
        tool_set        = final_tools,
        tools_manager   = tools_manager,
        session         = session,
        context_presser = ContextCompresser()
    )
    
    # 5. 选择模型
    caller.change_model(model_name="gpt-4")
    
    # 6. 开始对话...
```

---

## 项目结构 📁

```
aioclaw/
├── src/
│   └── aioclaw/
│       ├── core/              # 核心逻辑
│       │   ├── assistant_caller.py   # AI 助手调用器
│       │   └── context_compresser.py # 上下文压缩器
│       ├── errors/            # 异常体系
│       │   ├── base_claw_error.py
│       │   └── assistant_errors/     # 助手相关异常
│       ├── tools/             # 工具实现
│       │   ├── code_operation_tools.py    # 代码执行工具
│       │   ├── file_operation_tools.py    # 文件操作工具
│       │   ├── network_operation_tools.py # 网络请求工具
│       │   ├── skill_operation_tools.py   # 技能操作工具
│       │   ├── system_operation_tools.py  # 系统操作工具 (TODO)
│       │   └── _final_tools.py           # 工具聚合器
│       ├── managers/          # 管理器
│       │   ├── tools_manager.py   # 工具注册与执行管理
│       │   ├── models_manager.py  # 模型配置管理
│       │   ├── skills_manager.py  # 技能管理
│       │   └── keys_manager.py    # API Key 管理
│       ├── protocols/         # 抽象协议层
│       │   ├── tools_manager_protocol.py
│       │   ├── models_manager_protocol.py
│       │   ├── skills_manager_protocol.py
│       │   ├── context_compress_protocol.py
│       │   └── tool_set_protocol.py
│       ├── models/            # 数据模型
│       │   ├── skill.py               # 技能模型
│       │   ├── assistant_prompt.py     # 提示词管理
│       │   ├── assistant_output.py     # 输出模型
│       │   ├── context_compress_result.py
│       │   ├── config_models/         # 配置模型
│       │   └── runtime_models/        # 运行时模型
│       ├── enums/             # 枚举
│       │   ├── file_types.py
│       │   └── execute_status.py
│       └── utils/             # 工具函数
│           ├── event_waiter.py
│           └── syntax_sugar.py
├── pyproject.toml
└── README.md
```

---

## 核心模块说明 📖

### 1️⃣ Core - 核心层

#### AssistantCaller 🧠
AI 助手的核心调用器，负责：
- 多轮对话管理（含轮次限制）
- 模型动态切换 (`change_model`)
- 工具调用与结果回填
- 上下文压缩触发
- 提示词注入

#### ContextCompresser 📏
上下文窗口溢出处理器，当 token 超限时自动压缩上下文。

---

### 2️⃣ Tools - 工具集

| 工具集 | 功能 |
|--------|------|
| **CodeOperationTools** | 运行 Python 代码、执行 Bash 指令 |
| **FileOperationTools** | 读写文件、复制/删除、创建目录、搜索文件内容 |
| **NetworkOperationTools** | 发起 HTTP 请求、网页内容转 Markdown |
| **SkillOperationTools** | 搜索技能、读取/学习技能 |
| **SystemOperationTools** | 系统操作（开发中...） |

> 💡 使用 `chain_tools_by_instance()` 或 `chain_tools_by_class()` 快速组合多个工具集~

---

### 3️⃣ Managers - 管理器层

- **ToolsManager** — 注册工具函数与 Schema，安全执行工具调用
- **ModelsManager** — 根据名称/别名/URL 查找模型配置
- **SkillsManager** — 技能的新增、删除、关键词检索
- **KeysManager** — API Key 缓存与可用性轮询

---

### 4️⃣ Models - 数据模型

| 模型 | 说明 |
|------|------|
| `ClawConfig` | 顶层配置，聚合模型、路径、技能、运行时配置 |
| `PathConfig` | 文件/目录路径配置，自动读取文件或创建目录 |
| `SkillsDirectoryConfig` | 技能目录配置，自动扫描 `.md` 文件加载技能 |
| `AssistantRuntimeConfig` | 运行时参数（最大轮次、超时） |
| `AssistantRuntime` | 运行时状态跟踪 |
| `ToolRuntime` | 单个工具的执行状态跟踪 |
| `Skill` | 技能模型（支持 Markdown 前页元数据解析） |
| `AssistantPrompt` | 提示词管理（系统提示词 + 人设 + 已学技能） |
| `AssistantOutput` | AI 输出模型 |
| `ContextCompressResult` | 上下文压缩结果 |

---

### 5️⃣ Protocols - 协议层

所有核心组件均通过抽象协议定义接口，方便替换实现：

- `ToolsManagerProtocol` — 工具管理器接口
- `ModelsManagerProtocol` — 模型管理器接口
- `SkillsManagerProtocol` — 技能管理器接口
- `ContextCompressProtocol` — 上下文压缩器接口
- `ToolSetProtocol` — 工具集接口

---

### 6️⃣ Errors - 异常体系

```
BaseClawError
└── BaseAssistantError
    ├── ClientNotReady        # 客户端未就绪
    ├── MaxRoundLimit         # 超出对话轮次限制
    ├── AssistantCallError    # AI 调用失败
    ├── ModelConfigNotFound   # 模型配置未找到
    └── UnknownResponseType   # 未知响应类型
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
    NetworkOperationTools()
)
```

### 类组合（Mixin）
```python
from aioclaw.utils.syntax_sugar import chain_tools_by_class

MyToolSet = chain_tools_by_class(
    CodeOperationTools,
    FileOperationTools,
    name="MyToolSet"
)
```

---

## 配置示例 ⚙️

```python
from aioclaw.models.config_models import ClawConfig

config = ClawConfig.from_file("config.json")

# config.models_config          # 模型配置列表
# config.paths_config           # 路径配置列表  
# config.skills_config          # 技能目录配置
# config.assistant_runtime_config  # 运行时配置
```

---

## 许可证 📄

MIT License ~ 杂鱼们随便用哦！(๑¯◡¯๑)

---

> **Made with ❤️ by 喵璃也认可的开发者们~**
