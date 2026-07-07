from aioverse.managers	import ContextManager

from ..models	import _ClawContextsStatus

from typing	import Optional


class ClawContextManager(ContextManager):
	
	def __init__(self, contexts_status: Optional[_ClawContextsStatus] = None):
		
		self.contexts_status = contexts_status or _ClawContextsStatus()
	
	@property
	def token(self) -> int:
		
		"""
		优先通过context.token计算
		为0时返回self.contexts_status.token
		"""
		
		tokens = sum([ctx.token for ctx in self.contexts_status.flatten_contexts()])
		
		return tokens if tokens else self.contexts_status.token