from abc	import ABC, abstractmethod
from typing	import List, TYPE_CHECKING

from aioverse.base_models.tool_schema	import Tool
from aioverse.base_models.tool_calling	import ToolCalling
from aioverse.base_models.contexts		import ToolOutput


class ToolsManagerProtocol(ABC):
	
	@abstractmethod
	def register(self, tool_func: callable, tool_schema: Tool):
		
		"""实现工具注册"""
		
		...
	
	@abstractmethod
	async def execute_tool(self, tool_calling: ToolCalling) -> ToolOutput:
		
		"""运行工具并返回工具上下文"""
		
		...
	
	@abstractmethod
	def to_list(self) -> List[Tool]:
		
		"""返回Tool schema列表"""
		
		...