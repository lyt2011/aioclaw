from aioclaw.protocols	import ToolSetProtocol, ToolsManagerProtocol

from typing	import TYPE_CHECKING


# TODO 好像没啥用先不做了
class SystemOperationTools(ToolSetProtocol):
	
	def __init__(self, *args, **kwargs):
		
		super().__init__(*args, **kwargs)
	
	def register(self, tools_manager: ToolsManagerProtocol):
		
		super().register(tools_manager)
		
		...
	
	