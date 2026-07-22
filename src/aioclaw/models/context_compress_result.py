# 类型两件套
from pydantic	import BaseModel

from typing		import Optional


class ContextCompressResult(BaseModel):
		
	is_out			: bool
	is_compressed	: bool