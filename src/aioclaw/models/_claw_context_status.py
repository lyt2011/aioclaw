from aioverse.models	import _ContextsStatus

from pydantic	import PrivateAttr


class _ClawContextsStatus(_ContextsStatus):
	
	"""重写_ContextStatus 使其支持加压缩锁"""
	
	_is_compressing: bool = PrivateAttr(default=False)
	
	def is_compressing(self):
		return self._is_compressing