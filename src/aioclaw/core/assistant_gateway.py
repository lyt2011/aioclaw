from __future__ import annotations

from aioverse.holder	import NullObject
from aioverse.OpenAI	import OpenAIClient
from aioverse.models	import (
	BaseSegment,
	BaseContext,
	SystemContext,
	UserContext,
	ToolCallingContext,
	AssistantContext,
	Request,
	Response,
	StreamChunk,
	Delta
)

from .token_tracker	import TokenTracker, token_tracker
from .compresser	import Compresser
from ..models		import (
	ClawConfig,
	AssistantPrompt,
	AssistantSession,
	AssistantModelConfig,
	BaseContextsBlock,
	AssistantOutput,
	ToolCallingContextsBlock
)
from ..managers		import (
	ToolsManager,
	KeysManager
)
from ..errors		import (
	BaseGatewayError,
	UnknownFinishReasonError,
	RuntimeInputAdditionError,
	ModelConfigMissingError,
	IncompleteToolCallBlockError,
	GatewayBusyError
)
from ..factories	import (
	contexts_factory # 使用全局单例
)
from ..enums		import (
	FinishReasons
)
from ..utils		import (
	generate_assistant_output_by_response
)
from ..mixins		import (
	ValueNotifier
)
from .stream_handler	import StreamHandler

from typing	import Optional, Union, Iterator, List

import asyncio
import aiohttp


class AssistantGateway(ValueNotifier):

	def __init__(
		self,
		*,
		claw_config			: ClawConfig,
		assistant_session	: AssistantSession,
		openai_client		: Optional[OpenAIClient]	= None,
		tools_manager		: Optional[ToolsManager]	= None,
		assistant_prompt	: Optional[AssistantPrompt]	= None,
		token_tracker		: Optional[TokenTracker]	= None,
		compresser			: Optional[Compresser]		= None,
		stream_handler		: Optional[StreamHandler]	= None
	):

		# 必须参数
		self.claw_config		= claw_config
		self.assistant_session	= assistant_session

		# 可通过setter设置 且为可选参数
		self._openai_client		= openai_client
		self._assistant_prompt	= assistant_prompt
		self._tools_manager		= tools_manager
		self._token_tracker		= token_tracker
		self._compresser		= compresser
		self._stream_handler	= stream_handler

		# 网关内部变量 不可通过__init__参数传递 但有setter
		self._keys_manager			: KeysManager			= None
		self._assistant_model_config: AssistantModelConfig	= None

		# 网关内部变量 无setter
		self._client_session: aiohttp.ClientSession = None

		# 网关状态
		self._is_round_processing		: bool	= False
		self._is_generator_processing	: bool	= False
		self._is_stopping_generator		: bool	= False



	def set_assistant_model_config(self, assistant_model_config: AssistantModelConfig):
		self._assistant_model_config = assistant_model_config
	def set_assistant_prompt(self, assistant_prompt: AssistantPrompt):
		self._assistant_prompt = assistant_prompt
	def set_keys_manager(self, keys_manager: KeysManager):
		self._keys_manager = keys_manager
	def set_tools_manager(self, tools_manager: ToolsManager):
		self._tools_manager = tools_manager
	def set_token_tracker(self, token_tracker: TokenTracker):
		self._token_tracker = token_tracker
	def set_compresser(self, compresser: Compresser):
		self._compresser = compresser
	def set_openai_client(self, openai_client: OpenAIClient):
		self._openai_client = openai_client
	def set_stream_handler(self, stream_handler: StreamHandler):
		self._stream_handler = stream_handler



	def set_processing(self, status: bool):
		self.change("_is_round_processing", status)
	def set_generator_processing(self, status: bool):
		self.change("_is_generator_processing", status)
	def set_stop_generator(self, status: bool):
		self.change("_is_stopping_generator", status)



	def change_model(self, model_name: str) -> bool:

		"""
		通过遍历模型列表并比对模型名来更换模型
		成功返回True 失败返回False
		"""

		for assistant_model_config in self.claw_config.models_config:

			if assistant_model_config.model_name == model_name:
				self.set_assistant_model_config(assistant_model_config)
				self.set_keys_manager(KeysManager(assistant_model_config.model_keys))
				return True

		return False



	async def input(self, context: BaseContext):

		"""
		接收外部输入添加上下文
		会经过on_adding_context校验
		"""

		if self.is_round_processing is True:
			raise RuntimeInputAdditionError(f"不可在运行时添加新的输入")

		await self.on_adding_context(context)

	async def wait_for_round_process(self, timeout: int = 30):

		"""封装 asyncio.wait_for 等待一轮调用结束"""

		async def _wait():
			while self.is_round_processing:
				await self.wait_change()

		await asyncio.wait_for(_wait(), timeout=timeout)

	async def wait_for_generator_process(self, timeout: int = 180):

		"""封装 asyncio.wait_for 等待生成器结束"""

		async def _wait():
			while self.is_generator_processing:
				await self.wait_change()

		await asyncio.wait_for(_wait(), timeout=timeout)



	@property
	def token_tracker(self) -> TokenTracker:

		"""
		token追踪器懒加载
		默认返回aioclaw全局单例
		"""

		if self._token_tracker is None:
			return token_tracker

		return self._token_tracker

	@property
	def compresser(self) -> Compresser:

		if self._compresser is None:
			return NullObject() # TODO: 上下文压缩机制还没写好

		return self._compresser

	@property
	def keys_manager(self) -> KeysManager:

		"""
		懒加载 KeysManager
		若未设置则生成空的 KeysManager 并返回
		"""

		if self._keys_manager is None:
			keys_manager = KeysManager()
			self.set_keys_manager(keys_manager)

		return self._keys_manager

	@property
	def assistant_prompt(self) -> AssistantPrompt:

		"""
		懒加载 AI提示词
		若未设置 则使用默认提示词
		"""

		if self._assistant_prompt is None:
			assistant_prompt = AssistantPrompt()
			self.set_assistant_prompt(assistant_prompt)

		return self._assistant_prompt

	@property
	def tools_manager(self) -> ToolsManager:

		"""
		懒加载 ToolsManager
		若未设置 则设置为一个空的 ToolsManager 并返回
		"""

		if self._tools_manager is None:
			tools_manager = ToolsManager()
			self.set_tools_manager(tools_manager)

		return self._tools_manager

	@property
	def assistant_model_config(self) -> AssistantModelConfig:

		"""
		懒加载 AI配置
		若当前没有设置任何的模型配置
		则默认使用 claw_config 首个模型配置
		"""

		if self._assistant_model_config is None:

			if not self.claw_config.models_config:
				raise ModelConfigMissingError("无任何可用模型的信息")

			default_model_config = self.claw_config.models_config[0]
			self.change_model(default_model_config.model_name)

		return self._assistant_model_config

	@property
	def client_session(self) -> aiohttp.ClientSession:

		if self._client_session is None:
			client_session = aiohttp.ClientSession()
			self._client_session = client_session

		return self._client_session

	@property
	def openai_client(self) -> OpenAIClient:

		if self._openai_client is None:
			openai_client = OpenAIClient(session=self.client_session)
			self.set_openai_client(openai_client)

		return self._openai_client
	
	@property
	def stream_handler(self) -> StreamHandler:
		
		if self._stream_handler is None:
			self._stream_handler = StreamHandler()
		
		return self._stream_handler



	@property
	def is_round_processing(self) -> bool:
		return self._is_round_processing
	@property
	def is_stopping_generator(self) -> bool:
		return self._is_stopping_generator
	@property
	def is_generator_processing(self) -> bool:
		return self._is_generator_processing



	async def on_adding_context(self, context: BaseContext) -> None:

		"""事件钩子 添加上下文的回调"""

		self.assistant_session.contexts_status.add_context(context)

	async def on_adding_context_block(self, context_block: BaseContextsBlock) -> None:

		"""事件钩子 添加上下文块"""

		self.assistant_session.contexts_status.add_context(context_block)

	async def on_tool_calling(self, context: ToolCallingContext) -> None:

		"""事件钩子 tool calling时回调"""

		contexts_block = ToolCallingContextsBlock(tool_calling=context)

		for tool_call in context.tool_calls:

			logger.debug(
				f"Tool {tool_call.function.name} executing "
				f"with arguments: {tool_call.function.arguments}"
			)

			tool_output = await self.tools_manager.execute_tool(tool_call)
			contexts_block.append(tool_output)

		if contexts_block.is_complete() is False:
			raise IncompleteToolCallBlockError("tool calling block 完整性验证失败")

		await self.on_adding_context_block(contexts_block)

	async def on_context(self, context: BaseContext) -> None:

		"""事件钩子 普通上下文回调"""

		await self.on_adding_context(context)

	async def on_build_request(self) -> Request:

		"""事件钩子 用于生成请求模型"""

		request_model = Request(url=self.assistant_model_config.api_url)

		# 先插入基础信息
		request_model.set_header("Authorization", self.keys_manager.get_available_key().key)
		request_model.set_header("Content-Type", "application/json")
		request_model.set_body("model", self.assistant_model_config.model_name)
		request_model.set_body("messages", self.assistant_session.contexts_status.to_list())
		request_model.set_body("stream", self.assistant_model_config.support_streaming)

		# Tool Calling 支持判断
		if self.assistant_model_config.support_tool is True:
			request_model.set_body("tools", self.tools_manager.to_list())

		# Thinking 支持判断
		if self.assistant_model_config.support_thinking is True:
			request_model.set_body("thinking", {"type": self.assistant_session.assistant_think_mode})
			request_model.set_body("reasoning_effort", self.assistant_session.assistant_think_effort)

		return request_model

	async def on_request(self, request: Request) -> Response:

		"""事件钩子 用于请求"""

		response = await self.openai_client.call(request=request)
		return response

	async def on_response(self, response: Response) -> None:

		"""事件钩子 返回后对response作处理"""

		context			= contexts_factory.dispatcher(response.choices[0].message.model_dump())
		finish_reason	= response.choices[0].finish_reason


		if response.usage is not None:
			total_tokens = response.usage.total_tokens
			self.assistant_session.contexts_status.set_token(total_tokens)

		if finish_reason == FinishReasons.TOOL_CALLING:
			await self.on_tool_calling(context)

		elif finish_reason == FinishReasons.STOP:
			await self.on_context(context)

			if self.is_generator_processing:
				self.set_stop_generator(True)

		else:
			raise UnknownFinishReasonError(f"未处理的finish_reason: {finish_reason}")

	async def on_stream_chunk(self, chunk: StreamChunk) -> Optional[AssistantOutput]:

		"""处理流式数据块, 返回 AssistantOutput 表示本轮结束, None 表示继续"""

		if not chunk.choices:
			return None

		choice = chunk.choices[0]
		delta = choice.delta

		self.stream_handler.merge(delta)

		if choice.finish_reason is None:
			return None

		finish_reason = choice.finish_reason
		handler = self.stream_handler

		if finish_reason == FinishReasons.TOOL_CALLING:
			await self.on_tool_calling(handler.build_tool_calling_context())
			handler.reset()
			return None

		elif finish_reason == FinishReasons.STOP:
			assistant_ctx = AssistantContext(
				role="assistant",
				content=handler._content,
				reasoning_content=handler._reasoning
			)
			await self.on_context(assistant_ctx)

			if self.is_generator_processing:
				self.set_stop_generator(True)

			return handler.flush()

		else:
			raise UnknownFinishReasonError(f"未处理的finish_reason: {finish_reason}")


	async def on_build_output(self, response: Response) -> Optional[AssistantOutput]:

		"""
		事件钩子
		基于response与self生成AssistantOutput
		如果返回None则跳过本次yield
		否则yield本函数返回的结果
		"""

		return generate_assistant_output_by_response(response)

	async def on_stream_request(self) -> Union[AssistantOutput, None]:

		"""流式请求路径 (可被子类重写)"""

		request			= await self.on_build_request()
		contexts_status	= self.assistant_session.contexts_status

		async for chunk in self.openai_client.call_stream(request=request):

			if chunk.usage is not None:
				contexts_status.set_token(chunk.usage.total_tokens)

			if output := await self.on_stream_chunk(chunk):
				return output

		# 流结束, 检查是否有未刷新的内容
		if not self.stream_handler.is_empty:
			return self.stream_handler.flush()

		return None

	async def on_common_request(self) -> Union[AssistantOutput, None]:

		"""非流式请求路径 (可被子类重写)"""

		request		= await self.on_build_request()
		response	= await self.on_request(request)
		
		await self.on_response(response)
		return await self.on_build_output(response)

	async def on_round_initiate(self) -> None:

		"""事件钩子 请求前对self的数据做校验/处理"""

		if self.is_round_processing is True:
			raise GatewayBusyError("网关正在工作")
		else:
			self.set_processing(True)

		# 每轮开始时重置流式缓存
		self.stream_handler.reset()

		# 如果提示词与gateway的提示词不是同一个对象则设置提示词
		if not (self.assistant_session.contexts_status.prompt is self.assistant_prompt):
			system_context = SystemContext(content=self.assistant_prompt.model_dump_json())
			self.assistant_session.contexts_status.set_prompt(system_context)

		# 模型不一致时切换模型
		if self.assistant_model_config.model_name != self.assistant_session.assistant_model_name:
			self.change_model(self.assistant_session.assistant_model_name)


	async def on_round_complete(self) -> None:

		"""
		事件钩子
		**单次**请求完成后对self的处理
		注意与 on_generator_end 区分
		"""

		if self.is_round_processing is True:
			self.set_processing(False)

		contexts_status = self.assistant_session.contexts_status # 太jb长了单独拎出来

		guessed = await asyncio.to_thread(
			self.token_tracker.estimate,
			[ctx.model_dump_json(exclude_none=True) for ctx in contexts_status.flatten_contexts()]
		)
		self.token_tracker.calibrate_ratio(guessed=guessed, actual=contexts_status.token)

		logger.debug(f"估算 tokens: {guessed}")
		logger.debug(f"实际 tokens: {contexts_status.token}")
		logger.debug(f"当前平均差值: {self.token_tracker.ratio}")

	async def on_round_error(self, exception: Exception) -> None:

		"""事件钩子 对请求中出现的错误处理"""

		raise exception # HACK: 贪方便先直接再次抛出 到时候慢慢搞


	async def on_generator_initiate(self) -> None:

		"""事件钩子 生成器开始时执行的工作"""
		self.set_generator_processing(True)

	async def on_generator_end(self) -> None:

		"""事件钩子 生成器停止时执行"""
		self.set_generator_processing(False)

	async def on_generator_error(self, exception: Exception) -> None:

		"""事件钩子 生成器出现错误时执行"""

		raise exception # HACK: 依旧懒得弄


	async def on_gateway_close(self) -> None:

		"""事件钩子 当 gateway 关闭时由调用方手动执行"""

		await self.client_session.close()


	async def round_call(self) -> Union[AssistantOutput, None]:

		"""
		在 on_round_initiate 钩子中 processing 被设为 True
		在 finally 中 on_finish 钩子中 processing 被设为 False
		单次生成的完整生命周期
		"""

		await self.on_round_initiate()

		try:
			if self.assistant_model_config.support_streaming:
				return await self.on_stream_request()
			else:
				return await self.on_common_request()

		except Exception as e:
			await self.on_round_error(e)

		finally:
			await self.on_round_complete()
	
	async def async_generator(self) -> Iterator[AssistantOutput]:

		"""异步生成器 多次调用 self.round_call 实现工作完整流程"""

		await self.on_generator_initiate()

		try:

			while True:

				if (result := await self.round_call()):
					yield result

				if self.is_stopping_generator:
					self.set_stop_generator(False)
					break

		except GeneratorExit:
			raise

		except Exception as e:
			await self.on_generator_error(e)

		finally:
			await self.on_generator_end()