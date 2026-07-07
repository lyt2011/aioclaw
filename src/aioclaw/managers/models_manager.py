from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from ..protocols import ModelsManagerProtocol

if TYPE_CHECKING:
	
	from aioverse.base_models import ModelConfig


class ModelsManager(ModelsManagerProtocol):
	
	def __init__(self, models_config: List[ModelConfig]):
		
		self.models_config = models_config
	
	def __len__(self) -> int:
		
		return len(self.models_config)
		
	def find_model(
		self,
		model_name	: Optional[str] = None,
		model_alias	: Optional[str] = None,
		api_url		: Optional[str] = None
	) -> ModelConfig | None:
		
		for model_config in self.models_config:
			
			# 通过all实现3条件一起验证
			if all((
				model_name	is None or model_config.model_name == model_name,
				model_alias	is None or model_config.model_alias == model_alias,
				api_url		is None or model_config.api_url == api_url
			)):
			
				return model_config
			
		return None
	
	def to_list(self) -> List[ModelConfig]: return self.models_config # 可修改