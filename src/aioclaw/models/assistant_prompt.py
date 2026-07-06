# 类型两件套
from pydantic	import BaseModel, Field
from typing		import List, Dict, Any, Optional, Self

import orjson
import datetime


# 系统提示词需要直接硬编码
# 你可以修改 但是不建议
system_prompt = (
"""
# 提示词 {#Prompt}

## 优先级 **从高到低** (内容冲突时优先级更高的生效)
1. `system_prompt`: 系统提示词
2. `learned_skills`: 缓存已学习过的 skill 信息 `{<技能名>: <技能描述>, ...}`
3. `role_prompt`: 人设提示词

# 核心逻辑 **处理过程必须完整按照该步骤进行**
1. 接收用户输入
2. 根据用户输入提取技能搜索关键词并搜索技能
  - 得到结果 -> 读取技能并判断与用户需求相关性
    - 相关性高 -> 学习并根据技能规定处理用户需求
    - 相关性低 -> 跳过
  - 未得到结果 -> 尝试通过自己的能力解决用户需求
3. 根据`role_prompt`生成输出

# 工具 {Tool}

## 工具执行顺序
工具采用**顺序异步堵塞**执行，**理论上**不存在竞态

# 约束

## 文件删改约束
1. 在尝试修改/删除一个文件时，**必须**询问用户是否同意该操作，**用户同意后方可继续**
2. **严禁**在未经用户同意前擅自删除/修改文件
"""
)


class AssistantPrompt(BaseModel):
	
	system_prompt	: str = system_prompt
	role_prompt		: str = ""
	learned_skills	: Dict[str, str] = Field(default_factory=dict) # 技能名: 技能描述
	metadata		: Dict[str, Any] = Field(default_factory=dict, exclude=True)
	
	def set_system_prompt(self, prompt: str) -> Self:
		self.system_prompt = prompt
		return self
	def set_role_prompt(self, prompt: str) -> Self:
		self.role_prompt = prompt
		return self
	def add_metadata(self, key: str, value: Any) -> Self:
		self.metadata[key] = value
		return self
	
	def to_json(self) -> str:
		
		return orjson.dumps({
			"system_prompt"	: self.system_prompt,
			"role_prompt"	: self.role_prompt,
			"learned_skills": self.learned_skills,
			**self.metadata
		}).decode()