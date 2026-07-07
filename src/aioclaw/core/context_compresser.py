from ..protocols		import ContextCompressProtocol
from ..models			import ContextCompressResult
from .assistant_caller	import AssistantCaller

from aioverse.models	import ModelConfig
from aioverse.managers	import ContextManager


class ContextCompresser(ContextCompressProtocol):
	
	def __init__(self):
		
		"""需要任意 assistant_caller 实现AI请求"""
			
	# 判断溢出
	async def _is_out(self, context_manager: ContextManager, model_config: ModelConfig) -> bool:
	
		return context_manager.token >= model_config.token_limit
	
	async def _compress(self, context_manager: ContextManager, model_config: ModelConfig) -> bool:
		
		"""这里放清理逻辑"""
				
		context_manager.trim()
				
		return True
	
	async def compress(self, **kwargs) -> ContextCompressResult:
		
		# 是否需要清理
		is_out			= await self._is_out(**kwargs)
		is_compressed	= await self._compress(**kwargs) if is_out else False
		
		return ContextCompressResult(
			is_out			= is_out,
			is_compressed	= is_compressed
		)