from __future__ import annotations

from abc	import ABC, abstractmethod
from typing	import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
	
	from aioverse.models import ModelConfig


class ModelsManagerProtocol(ABC):
	
	@abstractmethod
	def find_model(
		self,
		model_name	: str,
		api_url		: Optional[str] = None,
		model_alias	: Optional[str] = None
	) -> ModelConfig | None:
		
		"""找模型配置"""
		
		...