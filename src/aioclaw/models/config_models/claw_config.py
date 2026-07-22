from __future__ import annotations

from pydantic	import Field

from .assistant_model_config	import AssistantModelConfig
from .assistant_runtime_config	import AssistantRuntimeConfig
from .base_config				import BaseConfig
from .path_config				import PathConfig
from .skills_directory_config	import SkillsDirectoryConfig

from typing		import List


class ClawConfig(BaseConfig):
	
	models_config: List[AssistantModelConfig] = Field(default_factory=list)
	
	paths_config	: List[PathConfig]		= Field(default_factory=list)
	skills_config	: SkillsDirectoryConfig	= Field(default_factory=SkillsDirectoryConfig)
	
	assistant_runtime_config: AssistantRuntimeConfig = Field(default_factory=AssistantRuntimeConfig)