from aioclaw.protocols	import ContextCompressProtocol
from aioclaw.models		import ContextCompressResult

from aioverse.base_models	import ModelConfig
from aioverse.managers		import ContextManager


class ContextCompresser(ContextCompressProtocol):
	
	# init暂时无用
	def __init__(self): pass
	
	# 判断溢出
	def _is_out(
		self,
		context_manager	: ContextManager,
		model_config	: ModelConfig
	) -> bool:
		
		return context_manager.token >= model_config.token_limit
	
	async def _compress(
		self,
		context_manager	: ContextManager,
		model_config	: ModelConfig
	) -> bool:
		
		"""这里放清理逻辑"""
				
		context_manager.trim()
				
		return True
	
	async def compress(self, **kwargs) -> ContextCompressResult:
		
		# 是否需要清理
		is_out = self._is_out(**kwargs)
		
		is_compressed = (
			False if not is_out
			else await self._compress(**kwargs)
		)
		
		return ContextCompressResult(
			is_out			= is_out,
			is_compressed	= is_compressed
		)