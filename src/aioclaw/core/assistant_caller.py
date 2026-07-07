from aioverse.models		import (
	Response,
	Usage,
	ToolCallingBlock,
	ToolCalling,
	Context,
	Prompt,
	ToolCallingContext,
	ModelConfig
)
from aioverse.Log			import get_log
from aioverse.OpenAI		import OpenAIClient
from aioverse.protocols 	import LogProtocol

from ..protocols	import (
	ContextCompressProtocol,
	ModelsManagerProtocol,
	ToolsManagerProtocol,
	ToolSetProtocol
)
from ..errors		import (
	ClientNotReady,
	ModelConfigNotFound,
	AssistantCallError,
	MaxRoundLimit,
	UnknownResponseType
)
from ..models		import AssistantRuntime, AssistantOutput, AssistantPrompt
from ..managers		import KeysManager, ClawContextManager

from typing import List, Dict, Any, Optional, Tuple

import aiohttp
import asyncio


class AssistantCaller:
	
	"""通过实例注入使用"""
	
	def __init__(
		self,
		models_manager	: ModelsManagerProtocol,
		tool_set		: ToolSetProtocol,
		tools_manager	: ToolsManagerProtocol,
		session			: aiohttp.ClientSession,
		context_presser	: Optional[ContextCompressProtocol]	= None,
		assistant_prompt: Optional[AssistantPrompt]			= None,
		async_log		: Optional[LogProtocol]				= None
	):
		
		# 日志
		self.log = async_log or get_log("assistant_manager.log", "assistant_manager", True)
		
		self.session			= session
		self.assistant_prompt	= assistant_prompt # claw专用的提示词
		self.context_presser	= context_presser
		
		self.tools_manager	= tools_manager
		self.tool_set		= tool_set
		
		self.models_manager	= models_manager
		
		# 这里定义为None 通过change_model动态更换
		self.openai_client	= None
		self.model_config	= None
		self.keys_manager	= None
		
		# 状态
		self.is_changed_model = False
	
	def _update_token(
		self,
		context_manager	: ClawContextManager,
		new_context		: Context,
		usage			: Usage
	) -> None:
		
		"""更新本次对话的token数量"""
		
		# 计算本次消耗token API返回total_tokens - 上下文管理器中未更新的token
		current_request_token = usage.total_tokens - context_manager.token
		
		new_context.set_token(current_request_token)
		context_manager.set_token(usage.total_tokens)
		
		return None
	
	# 压缩上下文
	async def _press_context(self, context_manager: ClawContextManager):
		
		if not context_manager or not self.model_config:
			raise ClientNotReady("客户端未准备就绪")
		
		press_result	= await self.context_presser.compress(
			context_manager	= context_manager,
			model_config	= self.model_config
		)
		
		await self.log.log((
			f"上下文溢出: {press_result.is_out} "
			f"清理结果: {press_result.is_compressed}"
		), "info")
		
		return None
	
	def _update_prompt(self, context_manager: ClawContextManager) -> None:
		
		# 更新提示词
		if self.assistant_prompt is not None:
			
			prompt = Prompt(content=self.assistant_prompt.to_json())
			
			context_manager.set_prompt(prompt)
		
		return None
	
	async def _log_tool_call(self, tool_call: ToolCalling, max_length: int = 70) -> None:
		
		tool_name		= tool_call.function.name
		tool_arguments	= tool_call.function.arguments
		
		await self.log.log(f"{tool_name} -> {tool_arguments[:max_length]}")
	
	async def _tools_execute(self, tool_calling_ctx: ToolCallingContext) -> ToolCallingBlock:
		
		tool_calling_block = ToolCallingBlock(tool_calling=tool_calling_ctx)
		
		for tool_call in tool_calling_ctx.tool_calls:
			
			await self._log_tool_call(tool_call, 100)
			
			tool_output = await self.tools_manager.execute_tool(tool_call)
			
			tool_calling_block.append(tool_output)
		
		tool_calling_block.verify_tool_ids() # 对tool_call_id与tool_output_id进行验证
		
		return tool_calling_block
		
	async def _call_assistant(self, **kwargs) -> Response:
	
		"""内部ai调用函数 仅调用ai和处理错误"""

		if self.is_changed_model is False:
			raise ClientNotReady("未选择模型")
		
		# call AI 并注入工具
		response = await self.openai_client.call(**kwargs)
		
		return response
	
	def _generate_assistant_output(self, response: Response) -> AssistantOutput:
		
		output = AssistantOutput(
			response_type		= response.choices[0].finish_reason,
			content				= response.choices[0].message.content,
			reasoning_content	= response.choices[0].message.reasoning_content
		)
		
		return output
	
	def change_model(self, **kwargs) -> Tuple[bool, ModelConfig | None]:
		
		# 找模型
		model_config = self.models_manager.find_model(**kwargs)
		
		if model_config is not None:
			
			# 创建OpenAIClient
			self.openai_client	= OpenAIClient(
				model_config	= model_config,
				async_log		= self.log,
				session			= self.session
			)
			self.model_config	= model_config
			self.keys_manager	= KeysManager(model_config.model_keys)
			
			self.is_changed_model = True
						
			return True, model_config
					
		return False, self.model_config
	
	async def async_assistant_generator(
		self,
		context_manager		: ClawContextManager,
		assistant_runtime	: AssistantRuntime
	) -> AssistantOutput:
		
		# 更新提示词
		self._update_prompt(context_manager)
		
		while assistant_runtime.current_rounds <= assistant_runtime.max_rounds:
			
			assistant_runtime.add_round()
			
			await self._press_context(context_manager)
			
			response = await self._call_assistant(
				context_manager	= context_manager,
				assistant_key	= self.keys_manager.get_available_key(),
				timeout			= assistant_runtime.timeout,
				body			= {"tools": self.tools_manager.to_list()}
			)
			
			context		= response.choices[0].message
			response_T	= response.choices[0].finish_reason
			
			assistant_runtime.update_LRT(response_T) # 更新last_response_type
			
			if response.usage is not None:
				self._update_token(
					new_context		= context,
					context_manager	= context_manager,
					usage			= response.usage
				)
			
			# 生成输出
			yield self._generate_assistant_output(response=response)
						
			if response_T == "tool_calls":
					
				tool_calling_block = await self._tools_execute(context)
				
				context_manager.add_context(tool_calling_block)
				
				assistant_runtime.add_tool_calling_round()
				
			# 停止生成器	
			elif response_T == "stop":
				
				context_manager.add_context(context)
				
				return
			
			else: raise UnknownResponseType(f"未知的返回类型: {response_T}")
			
		await self.log.log(f"AI调用超过 {assistant_runtime.max_round} 次 已停止运行", "warn")
		
		raise MaxRoundLimit("超出调用次数限制")