# 类型两件套
from pydantic import model_validator, Field

from ..assistant_key	import AssistantKey
from .base_config		import BaseConfig

from typing import List, Optional, Dict, Any


class AssistantModelConfig(BaseConfig):
	
	api_url		: str
	model_name	: str
	model_keys	: List[AssistantKey] = Field(default_factory=list)
	
	max_context_length	: int = Field(..., description="模型明确的上下文长度")
	cleanup_threshold	: int = Field(..., description="触发清理逻辑的上下文长度")
	
	support_thinking	: bool	= Field(default=False, description="是否支持设置思考")
	support_tool		: bool	= Field(default=False, description="是否支持工具调用")
	support_streaming	: bool	= Field(default=True, description="是否支持流式输出")  # 🆕 默认开启
	support_image		: bool	= Field(default=False, description="是否支持图片理解")
	support_video		: bool	= Field(default=False, description="是否支持视频理解")
	support_audio		: bool	= Field(default=False, description="是否支持音频理解")
	
	# 实例化完成前
	@model_validator(mode="before")
	@classmethod
	def init_cleanup_threshold(self, data: Dict[str, Any]):
		
		max_context_length	= data.get("max_context_length")
		cleanup_threshold	= data.get("cleanup_threshold")
		
		if cleanup_threshold is None:
			
			if max_context_length is None:
				raise RuntimeError("上下文长度必须设置")
			
			data["cleanup_threshold"] = max_context_length * 0.75
		
		return data
