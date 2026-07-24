from __future__ import annotations
from .pydantic_models_factory	import PydanticModelsFactory
from aioverse.models	import (

	BaseContext,
	SystemContext,
	ToolCallingContext,
	ToolOutputContext,
	UserContext,
	AssistantContext
)


class ContextsFactory(PydanticModelsFactory):

	"""此处逻辑无需更改。"""
	...


# 全局单例 自动注册
# 注意注册顺序
# ToolCallingContext 的角色也是 assistant，所以要放在 AssistantContext 之前
contexts_factory = ContextsFactory()
contexts_factory.register(ToolCallingContext, 1)
contexts_factory.register(ToolOutputContext, 2)
contexts_factory.register(SystemContext, 3)
contexts_factory.register(AssistantContext, 4)
contexts_factory.register(UserContext, 5)
contexts_factory.register(BaseContext, 6)