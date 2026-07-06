from aioclaw.protocols	import ToolsManagerProtocol

from aioverse.base_models.tool_schema	import Tool
from aioverse.base_models.tool_calling	import ToolCalling
from aioverse.base_models.contexts		import ToolOutput

from typing import List, Dict, Tuple, Awaitable, Any, Callable

import orjson
import asyncio


# 辅助方法 安全的工具执行
async def safe_execute_tool(coro, timeout: int = 30) -> str:
	
	try:
		
		tool_output = await asyncio.wait_for(coro, timeout=timeout)
		
		return str(tool_output) # 保证返回str 防止api报错
	
	except Exception as e:
		
		return f"{type(e).__name__}: {e}"
	
# 辅助方法 函数转协程
def func2coro(func: callable, *args, **kwargs) -> Awaitable:

	return (
		func(*args, **kwargs)
		if asyncio.iscoroutinefunction(func)
		else asyncio.to_thread(func, *args, **kwargs)
	)


class ToolsManager(ToolsManagerProtocol):
	
	def __init__(self, timeout: int = 30):
		
		self.schema: Dict[str, Tuple[Callable, Tool]] = {}
		
		self.timeout = timeout
	
	def register(self, func: callable, schema: Tool):
				
		if func.__name__ not in self.schema:
			
			self.schema[func.__name__] = (func, schema)
		
		return None
	
	def set_timeout(self, timeout: int): self.timeout = timeout
	
	async def execute_tool(self, tool_calling: ToolCalling) -> ToolOutput:
		
		"""
		使工具调用不会崩溃 优化可读性
		"""
		
		tool_name	= tool_calling.function.name
		tool_id		= tool_calling.id
		
		if tool_name in self.schema:
		
			func, _			= self.schema[tool_name]
			tool_arguments	= orjson.loads(tool_calling.function.arguments)
			tool_coro		= func2coro(func, **tool_arguments)
			tool_output		= await safe_execute_tool(tool_coro, timeout=self.timeout)
		
		else:
			
			tool_output	= f"无法调用不存在的工具: {tool_name}"
		
		return ToolOutput(tool_call_id=tool_id, content=tool_output)
	
	def to_list(self) -> List[Dict[str, Any]]:
		
		return [schema.model_dump() for _, schema in self.schema.values()]