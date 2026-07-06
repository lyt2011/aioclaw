# 类型两件套
from pydantic	import BaseModel
from typing		import Optional


class AssistantOutput(BaseModel):
	
	response_type		: str
	content				: Optional[str]	= None
	reasoning_content	: Optional[str] = None