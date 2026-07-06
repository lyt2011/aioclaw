# 类型两件套
from pydantic	import BaseModel
from typing		import Dict, Optional, Any, Literal


class AssistantRuntime(BaseModel):
	
	"""运行时的配置"""
	
	timeout		: int = 300
	max_rounds	: int = 50

	current_rounds		: int = 0
	tool_calling_rounds	: int = 0
	
	# 上次返回的类型
	last_response_type: Optional[str] = None
	
	def add_round(self, count: int = 1): self.current_rounds += count
	def add_tool_calling_round(self, count: int = 1): self.tool_calling_rounds += count
	
	# 更新last_response_type
	def update_LRT(self, value: str): self.last_response_type = value