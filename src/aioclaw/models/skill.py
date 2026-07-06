# 类型两件套
from pydantic	import BaseModel, ConfigDict
from typing		import Dict, Optional, Any, Literal

# markdown解析实现
import frontmatter


class Skill(BaseModel):
	
	name		: str
	description	: str
	version		: Optional[str] = "0.1.0"
	content		: str
	
	@classmethod
	def from_markdown(cls, text: str) -> "cls":
		
		markdown = frontmatter.loads(text)
		
		return cls.model_validate({
			"name"			: markdown.get("name"),
			"description"	: markdown.get("description"),
			"version"		: markdown.get("version", "0"),
			"content"		: markdown.content.strip()
		})
	
	@classmethod
	def from_file(
		cls,
		path	: str,
		format	: Literal["markdown", "json"] = "markdown",
		encoding: str = "utf-8"
	) -> "cls":
		
		if format == "markdown":
			
			with open(path, "r", encoding=encoding) as file:
			
				markdown = file.read()
			
			return cls.from_markdown(markdown)
		
		else:
			
			with open(path, "rb") as file:
				
				json_bytes = file.read()
			
			return cls.model_validate(orjson.loads(json_bytes))