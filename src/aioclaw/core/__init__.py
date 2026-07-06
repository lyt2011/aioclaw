__all__ = [
	"AssistantCaller",
	"ContextCompresser"
]

# 顶层模块全部采用延迟导入
def __getattr__(name: str):
	
	if name == "AssistantCaller":
		
		from .assistant_caller	import AssistantCaller
		return AssistantCaller
		
	if name == "ContextCompresser":
		
		from .context_compresser	import ContextCompresser
		return ContextCompresser
	
	raise AttributeError(f"没有 {name} 这个模块")