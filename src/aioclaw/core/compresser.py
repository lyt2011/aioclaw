from __future__ import annotations

from ..models			import ContextCompressResult
from ..protocols		import ContextCompressProtocol
from aioverse.models	import BaseContext

from typing	import List


# FIXME: 这个类没做好不要用
# FIXME: 这个类没做好不要用
# FIXME: 这个类没做好不要用
# FIXME: 这个类没做好不要用
# FIXME: 这个类没做好不要用
# FIXME: 这个类没做好不要用
# FIXME: 这个类没做好不要用
# FIXME: 这个类没做好不要用
# FIXME: 这个类没做好不要用


class Compresser(ContextCompressProtocol):
	
	def __init__(self):
		
		"""需要任意 assistant_caller 实现AI请求"""
			
	# 判断溢出
	async def _is_out(self, current_tokens: int, cleanup_threshold: int) -> bool:
		return current_tokens >= cleanup_threshold
	
	async def _compress(self, contexts: List[BaseContext]) -> None:
		
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