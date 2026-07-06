from aioclaw.protocols import ToolSetProtocol

from aioclaw.tools._final_tools	import _FinalTools

from typing import Type

def chain_tools_by_class(*tool_classes, name: str="FinalTools") -> Type[ToolSetProtocol]:

	if not tool_classes:
		
		raise ValueError("至少需要一个工具类")
	
	return type(name, tool_classes, {})

def chain_tools_by_instance(*tool_instances) -> _FinalTools:
	
	return _FinalTools(*tool_instances)