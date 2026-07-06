from __future__ import annotations

from abc	import ABC, abstractmethod
from typing	import TYPE_CHECKING

if TYPE_CHECKING:

	from aioverse.managers		import ContextManager
	from aioverse.base_models	import ModelConfig
	
	from aioclaw.models	import ContextCompressResult


class ContextCompressProtocol(ABC):
	
	@abstractmethod
	def _is_out(self, context_manager: ContextManager, model_config: ModelConfig) -> bool:
		
		"""判断是否已经超限"""
		
		...
	
	@abstractmethod
	async def _compress(self, context_manager: ContextManager, model_config: ModelConfig) -> bool:
		
		"""对上下文进行压缩"""
		
		...
	
	@abstractmethod
	async def compress(self, context_manager: ContextManager, model_config: ModelConfig) -> ContextCompressResult:
		
		"""对外暴露的方法 自动进行判断及压缩"""
		
		...