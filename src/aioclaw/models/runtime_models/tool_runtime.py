from pydantic	import BaseModel, PrivateAttr, ConfigDict, SkipValidation, model_validator
from typing		import Dict, Any, Awaitable, Optional, Callable

from aioverse.models	import ToolOutput

from ...enums	import ExecuteStatus

import asyncio
import orjson


class ToolRuntime(BaseModel):
	
	"""单个工具的执行状态信息"""
	
	model_config = ConfigDict(arbitrary_types_allowed=True)
	
	tool_id			: str
	tool_name		: str
	tool_func		: SkipValidation[Callable]
	tool_arguments	: Dict[str, Any]
	tool_response	: str
	
	execute_status: ExecuteStatus = ExecuteStatus.hanging
	
	@model_validator(mode="before")
	@classmethod
	def _set_default_response(cls, data: Dict[str, Any]) -> Dict[str, Any]:
		
		data["tool_response"] = f"<TOOL RESPONSE id={data['tool_id']}>"
		
		return data
	
	def on_finish(self)	: self.execute_status = ExecuteStatus.finish
	def on_pending(self): self.execute_status = ExecuteStatus.pending
	def on_hanging(self): self.execute_status = ExecuteStatus.hanging
	def on_error(self)	: self.execute_status = ExecuteStatus.error
	
	# 辅助方法 函数转协程
	def _func2coro(self) -> Awaitable:
		
		return (
			self.tool_func(**self.tool_arguments)
			if asyncio.iscoroutinefunction(self.tool_func)
			else asyncio.to_thread(self.tool_func, **self.tool_arguments)
		)
	
	# 辅助方法 完成回调
	def _on_finish(self, task: asyncio.Task):
			
		# 尝试获取结果
		try:
			
			self.tool_response = task.result()
			
		except Exception as e:
			
			self.on_error()
			
			self.tool_response = f"{type(e).__name__}: {e}"
					
		else:
			
			self.on_finish()
		
		return None
	
	def execute_tool(self):
		
		coro = self._func2coro()
		task = asyncio.create_task(coro)
		task.add_done_callback(self._on_finish)
				
		self.on_pending()
		
		return None
	
	def model_dump(self) -> Dict[str, Any]:
		
		return ToolOutput(
			tool_call_id	= self.tool_id,
			content			= self.tool_response
		).model_dump()