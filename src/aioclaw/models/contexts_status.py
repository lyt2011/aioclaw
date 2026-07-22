from pydantic	import BaseModel, PrivateAttr, Field, SerializeAsAny

from .context_blocks	import BaseContextsBlock, ToolCallingContextsBlock
from aioverse.models	import BaseContext, SystemContext

from copy		import deepcopy
from typing		import List, Optional, Union, Dict, Any


ContextsListSupportType = List[Union[
	SerializeAsAny[ToolCallingContextsBlock],
	SerializeAsAny[BaseContextsBlock],
	SerializeAsAny[BaseContext]
]]


class ContextsStatus(BaseModel):
	
	contexts: ContextsListSupportType = Field(default_factory=list, description="上下文列表")
	prompt	: Optional[SystemContext] = Field(default=None, description="提示词")
	
	token	: int	= Field(default=0)
	
	_is_dirty		: bool = PrivateAttr(default=True)
	_contexts_cache	: List[SerializeAsAny[BaseContext]] = PrivateAttr(default_factory=list)
	
	
	def is_dirty(self) -> bool:
		return self._is_dirty
	
	
	def set_dirty(self, status: bool):
		self._is_dirty = status
	def set_token(self, token: int):
		self.token = token
	def set_prompt(self, prompt: Optional[SystemContext]):
		self.prompt = prompt
	def set_contexts_cache(self, contexts_list: List[BaseContext]):
		self._contexts_cache = contexts_list
	
	
	def _rebuild_contexts_cache_list(self) -> None:
		
		"""
		重建上下文缓存
		"""
		
		contexts_list = []
		
		for context in self.contexts:
			
			if isinstance(context, BaseContextsBlock):
				contexts_list.extend(ctx for ctx in context)
			else:
				contexts_list.append(context)
			
		self.set_contexts_cache(contexts_list)
		self.set_dirty(False)
		
	def add_context(self, context: Union[BaseContextsBlock, BaseContext]):
		self.contexts.append(context)
		self.set_dirty(True)
	
	def flatten_contexts(
		self, *,
		filter_prompt: bool = False
	) -> List[BaseContext]:
		
		"""自动根据_is_dirty 重建/不重建"""
		
		if self.is_dirty():
			self._rebuild_contexts_cache_list()
		
		# 有提示词就插入
		if self.prompt is not None and filter_prompt is False:
			prompt = SystemContext(content=self.prompt.model_dump_json())
			return [prompt, *self._contexts_cache]
		
		return self._contexts_cache
	
	def to_list(self, **kwargs) -> List[Dict[str, Any]]:
		
		"""转为列表"""
		
		contexts_list = [
			ctx.model_dump(mode="json", exclude_none=True)
			for ctx in self.flatten_contexts(**kwargs)
		]
		
		return contexts_list