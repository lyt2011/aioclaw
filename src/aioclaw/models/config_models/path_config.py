from __future__ import annotations

from pydantic	import PrivateAttr, model_validator
from typing		import Optional, Self

from .base_config	import BaseConfig
from ...enums		import FileTypes

import os


class PathConfig(BaseConfig):
	
	path: str
	type: FileTypes
	
	_content: Optional[str] = PrivateAttr(default=None)
	
	@property
	def content(self) -> str | None:
		return self._content
	
	def _read_file(self, **kwargs) -> None:
		
		"""读取之后直接让_file_content接收 不返回"""
		
		with open(self.path, **kwargs) as file:
			self._content = file.read()
		
		return None
	
	def _make_dirs(self, **kwargs) -> None:
		
		"""创建文件夹"""
		
		os.makedirs(self.path, **kwargs)
		
		return None
	
	@model_validator(mode="after")
	def init_object(self) -> Self:
	
		if self.type == FileTypes.file:
			self._read_file(encoding="utf-8")
		else:
			self._make_dirs(exist_ok=True)
		
		return self