from __future__ import annotations

from .base_config				import BaseConfig
from .skills_directory_config	import SkillsDirectoryConfig
from .assistant_runtime_config	import AssistantRuntimeConfig
from .path_config				import PathConfig

from aioverse.base_models	import ModelConfig

from typing		import List
from pydantic	import Field


class ClawConfig(BaseConfig):
	
	models_config: List[ModelConfig] = Field(default_factory=list)
	
	paths_config	: List[PathConfig]		= Field(default_factory=list)
	skills_config	: SkillsDirectoryConfig	= Field(default_factory=SkillsDirectoryConfig)
	
	assistant_runtime_config: AssistantRuntimeConfig = Field(default_factory=AssistantRuntimeConfig)