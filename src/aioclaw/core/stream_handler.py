from __future__ import annotations

from aioverse.models	import (
	Delta,
	ToolCalling as ToolCallingModel,
	ToolCallingContext
)

from ..models			import AssistantOutput
from ..enums			import FinishReasons

from typing		import List, Dict, Any, Optional


class StreamHandler:

	"""流式增量处理器 — 负责 SSE delta 累积与完整输出构建"""

	def __init__(self):
		self._content		: str				= ""
		self._reasoning		: str				= ""
		self._tool_calls	: List[Dict[str, Any]]	= []


	def reset(self) -> None:
		
		"""清空本轮增量缓存"""
		
		self._content	= ""
		self._reasoning	= ""
		
		self._tool_calls.clear()

	def merge(self, delta: Delta) -> None:
		
		"""将流式增量合并到缓存"""

		if delta.content:
			self._content += delta.content
		
		if delta.reasoning_content:
			self._reasoning += delta.reasoning_content
		
		if delta.tool_calls:
			for tc in delta.tool_calls:
				self._merge_tool_call(tc)

	def _merge_tool_call(self, tc: Dict[str, Any]) -> None:
		
		"""合并单个 tool_call delta 到缓存"""

		existing = self._find_tool_call(tc.get("index"))
		
		if existing is not None:
			self._update_tool_call(existing, tc)
		
		else:
			self._add_tool_call(tc)

	def _find_tool_call(self, index: Any) -> Optional[Dict[str, Any]]:
		
		"""按 index 查找已缓存的 tool_call"""
		
		for ptc in self._tool_calls:
			if ptc.get("index") == index:
				return ptc
		
		return None

	def _update_tool_call(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
		
		"""将 source 中的字段合并到 target"""
		
		for key in ("id", "type"):
			if source.get(key):
				target[key] = source[key]

		fn = source.get("function")
		if not fn:
			return

		target.setdefault("function", {})
		if fn.get("name"):
			target["function"]["name"] = fn["name"]
		if fn.get("arguments"):
			target["function"]["arguments"] = (
				target["function"].get("arguments", "") + fn["arguments"]
			)

	def _add_tool_call(self, tc: Dict[str, Any]) -> None:
		
		"""添加新的 tool_call 到缓存"""
		
		tc.setdefault("function", {})
		tc["function"].setdefault("name", "")
		tc["function"].setdefault("arguments", "")
		
		self._tool_calls.append(tc)

	def flush(self) -> AssistantOutput:
		
		"""从缓存构建完整输出 (不清空缓存)"""
		
		return AssistantOutput(
			finish_reason		= FinishReasons.STOP,
			content				= self._content,
			reasoning_content	= self._reasoning
		)

	def build_tool_calling_context(self):
		
		"""从缓存的 tool_calls 构建 ToolCallingContext"""
		
		tool_calls = [ToolCallingModel.model_validate(tc) for tc in self._tool_calls]

		return ToolCallingContext(
			role				= "assistant",
			content				= self._content,
			reasoning_content	= self._reasoning,
			tool_calls			= tool_calls
		)

	@property
	def is_empty(self) -> bool:
		return not (self._content or self._reasoning or self._tool_calls)
