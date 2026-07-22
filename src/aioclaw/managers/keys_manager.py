from __future__ import annotations

from ..errors	import NoKeyAvailableError

from typing import List, TYPE_CHECKING, Optional

if TYPE_CHECKING:
	
	from ..models	import AssistantKey


class KeysManager:
	
	def __init__(self, keys: Optional[List[AssistantKey]] = None):
		
		self.keys			= keys or []
		self._cached_key	= None
	
	def cache_key(self, key: AssistantKey):
		
		"""设置缓存的key"""
		
		self._cached_key = key
	
	def uncache_key(self):
		
		"""取消缓存key"""
		
		self._cached_key = None
	
	def _is_available_key(self, key: AssistantKey) -> bool:
		
		"""辅助方法 判断一个key是否已启用且可用"""
		
		return key.is_enable and key.is_available
	
	def get_available_key(self) -> Union[AssistantKey, None]:
	
		"""获取可用key"""
		
		# 尝试通过已缓存的key直接返回 O(1)实现
		if self._cached_key and self._is_available_key(self._cached_key): return self._cached_key
		
		for key in self.keys:
			
			if not self._is_available_key(key): continue
				
			# 找到则缓存该key并返回
			self.cache_key(key)
			return key
		
		raise NoKeyAvailableError(f"找不到可用的key")