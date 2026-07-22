from __future__ import annotations

from abc	import ABC, abstractmethod
from typing	import TYPE_CHECKING


if TYPE_CHECKING:

	from ..models	import ContextCompressResult


class ContextCompressProtocol(ABC):
	
	@abstractmethod
	async def _is_out(self, *args, **kwargs) -> bool:
		
		"""判断是否已经超限"""
		...
	
	@abstractmethod
	async def _compress(self, *args, **kwargs) -> bool:
		
		"""对上下文进行压缩"""
		...
	
	@abstractmethod
	async def compress(self, *args, **kwargs) -> ContextCompressResult:
		
		"""对外暴露的方法 自动进行判断及压缩"""
		...