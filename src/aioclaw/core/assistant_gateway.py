from __future__ import annotations

from aioverse.errors import ResponseCodeError
from aioverse.OpenAI import OpenAIClient
from aioverse.models import (
	BaseContext,
	SystemContext,
	ToolCallingContext,
	AssistantContext,
	Request,
	Response,
	StreamChunk,
)

from .token_tracker import TokenTracker, token_tracker
from .compresser import Compresser
from .stream_handler import StreamHandler
from ..models import (
	ClawConfig,
	AssistantPrompt,
	AssistantSession,
	AssistantModelConfig,
	BaseContextsBlock,
	AssistantOutput,
	ToolCallingContextsBlock,
	ContextCompressionPrompt,
)
from ..managers import ToolsManager, KeysManager
from ..errors import (
	UnknownFinishReasonError,
	RuntimeInputAdditionError,
	ModelConfigMissingError,
	IncompleteToolCallBlockError,
	GatewayBusyError,
)
from ..factories import contexts_factory
from ..enums import FinishReasons
from ..utils import generate_assistant_output_by_response
from ..mixins import ContextCompressionMixin, ValueNotifier

from typing import Optional, Union, Iterator

import asyncio
import logging
import time
import aiohttp


logger = logging.getLogger(__name__)


class AssistantGateway(ContextCompressionMixin, ValueNotifier):

	"""OpenAI 兼容的 Agent 网关，内置上下文压缩能力。"""

	def __init__(
		self, *,
		claw_config					: ClawConfig,
		assistant_session			: AssistantSession,
		openai_client				: Optional[OpenAIClient] = None,
		tools_manager				: Optional[ToolsManager] = None,
		assistant_prompt			: Optional[AssistantPrompt] = None,
		token_tracker				: Optional[TokenTracker] = None,
		compresser					: Optional[Compresser] = None,
		stream_handler				: Optional[StreamHandler] = None,
		context_compression_prompt	: Optional[ContextCompressionPrompt] = None,
	):
		
		self.claw_config = claw_config
		self.assistant_session = assistant_session

		super().__init__(
			compresser=compresser,
			context_compression_prompt=context_compression_prompt,
		)

		self._openai_client		= openai_client
		self._assistant_prompt	= assistant_prompt
		self._tools_manager		= tools_manager
		self._token_tracker		= token_tracker
		self._stream_handler	= stream_handler

		self._keys_manager			: Optional[KeysManager] = None
		self._assistant_model_config: Optional[AssistantModelConfig] = None

		self._client_session				: Optional[aiohttp.ClientSession] = None
		self._request_estimated_tokens		: Optional[int] = None
		self._request_prompt_tokens			: Optional[int] = None
		self._generator_start_timestamp		: Optional[float] = None
		self._generator_complete_timestamp	: Optional[float] = None
		self._retry_count = 0

		self._is_round_processing = False
		self._is_generator_processing = False
		self._is_stopping_generator = False

	def set_assistant_model_config(self, assistant_model_config: AssistantModelConfig):
		
		self._assistant_model_config = assistant_model_config
		
		if hasattr(self, "assistant_session"):
			self.assistant_session.contexts_status.clear_tokens_cache()

	def set_assistant_prompt(self, assistant_prompt: AssistantPrompt):
		
		self._assistant_prompt = assistant_prompt
		
		if hasattr(self, "assistant_session"):
			self.assistant_session.contexts_status.clear_tokens_cache()

	def set_keys_manager(self, keys_manager: KeysManager):
		self._keys_manager = keys_manager

	def set_tools_manager(self, tools_manager: ToolsManager):
		self._tools_manager = tools_manager

	def set_token_tracker(self, token_tracker: TokenTracker):
		
		self._token_tracker = token_tracker
		
		if hasattr(self, "assistant_session"):
			self.assistant_session.contexts_status.clear_tokens_cache()

	def set_openai_client(self, openai_client: OpenAIClient):
		self._openai_client = openai_client

	def set_stream_handler(self, stream_handler: StreamHandler):
		self._stream_handler = stream_handler

	def set_generator_start_timestamp(self, timestamp: Optional[float]):
		self._generator_start_timestamp = timestamp

	def set_generator_complete_timestamp(self, timestamp: Optional[float]):
		self._generator_complete_timestamp = timestamp



	def set_processing(self, status: bool):
		self.change("_is_round_processing", status)
	
	def set_generator_processing(self, status: bool):
		self.change("_is_generator_processing", status)
	
	def set_stop_generator(self, status: bool):
		self.change("_is_stopping_generator", status)



	def change_model(self, model_name: str) -> bool:
		"""切换到指定模型并重建对应的 Key 管理器。"""
		for assistant_model_config in self.claw_config.models_config:

			if assistant_model_config.model_name == model_name:
				self.set_assistant_model_config(assistant_model_config)
				self.set_keys_manager(KeysManager(assistant_model_config.model_keys))
				return True

		return False

	async def input(self, context: BaseContext):

		"""在网关空闲时添加外部输入。"""

		if self.is_round_processing:
			raise RuntimeInputAdditionError("不可在运行时添加新的输入")

		await self.on_adding_context(context)

	async def wait_for_round_process(self, timeout: int = 30):

		async def _wait():
			while self.is_round_processing:
				await self.wait_change()

		await asyncio.wait_for(_wait(), timeout=timeout)

	async def wait_for_generator_process(self, timeout: int = 180):

		async def _wait():
			while self.is_generator_processing:
				await self.wait_change()

		await asyncio.wait_for(_wait(), timeout=timeout)

	@property
	def token_tracker(self) -> TokenTracker:

		if self._token_tracker is None:
			return token_tracker

		return self._token_tracker

	@property
	def keys_manager(self) -> KeysManager:

		if self._keys_manager is None:
			self.set_keys_manager(KeysManager())

		return self._keys_manager

	@property
	def assistant_prompt(self) -> AssistantPrompt:

		if self._assistant_prompt is None:
			self.set_assistant_prompt(AssistantPrompt())

		return self._assistant_prompt

	@property
	def tools_manager(self) -> ToolsManager:

		if self._tools_manager is None:
			self.set_tools_manager(ToolsManager())

		return self._tools_manager

	@property
	def assistant_model_config(self) -> AssistantModelConfig:

		if self._assistant_model_config is None:

			if not self.claw_config.models_config:
				raise ModelConfigMissingError("无任何可用模型的信息")

			default_model_config = self.claw_config.models_config[0]

			if not self.change_model(default_model_config.model_name):
				raise ModelConfigMissingError(f"找不到默认模型: {default_model_config.model_name}")

		return self._assistant_model_config

	@property
	def client_session(self) -> aiohttp.ClientSession:

		if self._client_session is None:
			self._client_session = aiohttp.ClientSession()

		return self._client_session

	@property
	def openai_client(self) -> OpenAIClient:

		if self._openai_client is None:
			self.set_openai_client(OpenAIClient(session=self.client_session))

		return self._openai_client

	@property
	def stream_handler(self) -> StreamHandler:

		if self._stream_handler is None:
			self._stream_handler = StreamHandler()

		return self._stream_handler

	@property
	def generator_start_timestamp(self) -> Optional[float]:
		return self._generator_start_timestamp

	@property
	def generator_complete_timestamp(self) -> Optional[float]:
		return self._generator_complete_timestamp

	@property
	def generator_elapsed_seconds(self) -> Optional[float]:
		start_timestamp = self.generator_start_timestamp
		if start_timestamp is None:
			return None

		complete_timestamp	= self.generator_complete_timestamp
		end_timestamp		= complete_timestamp if complete_timestamp is not None else time.time()

		return max(end_timestamp - start_timestamp, 0.0)

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
		self.assistant_session.contexts_status.add_context(context)

	async def on_adding_context_block(self, context_block: BaseContextsBlock) -> None:
		self.assistant_session.contexts_status.add_context(context_block)

	async def on_tool_calling(self, context: ToolCallingContext) -> None:
		if not context.tool_calls:
			raise IncompleteToolCallBlockError("tool calling context 没有调用内容")

		contexts_block = ToolCallingContextsBlock(tool_calling=context)

		for tool_call in context.tool_calls:
			logger.info(
				"执行工具 %s，参数: %s",
				tool_call.function.name,
				tool_call.function.arguments,
			)
			tool_output = await self.tools_manager.execute_tool(tool_call)
			contexts_block.append(tool_output)

		if not contexts_block.is_complete():
			raise IncompleteToolCallBlockError("tool calling block 完整性验证失败")

		await self.on_adding_context_block(contexts_block)

	async def on_context(self, context: BaseContext) -> None:
		await self.on_adding_context(context)

	async def on_build_request(self) -> Request:

		request_model	= Request(url=self.assistant_model_config.api_url)
		assistant_key	= self.keys_manager.get_available_key()

		request_model.set_header("Authorization", assistant_key.key)
		request_model.set_header("Content-Type", "application/json")
		request_model.set_body("model", self.assistant_model_config.model_name)
		request_model.set_body("messages", self.assistant_session.contexts_status.to_list())
		request_model.set_body("stream", self.assistant_model_config.support_streaming)

		if self.assistant_model_config.support_tool:
			request_model.set_body("tools", self.tools_manager.to_list())

		if self.assistant_model_config.support_thinking:
			request_model.set_body("thinking", {"type": self.assistant_session.assistant_think_mode})
			request_model.set_body("reasoning_effort", self.assistant_session.assistant_think_effort)

		return request_model

	async def on_request(self, request: Request) -> Response:
		return await self.openai_client.call(request=request)

	async def on_response(self, response: Response) -> None:

		if not response.choices:
			raise UnknownFinishReasonError("模型响应没有 choices")

		choice			= response.choices[0]
		message			= choice.message
		context			= contexts_factory.dispatcher(message.model_dump())
		finish_reason	= choice.finish_reason

		if response.usage is not None:
			self.assistant_session.contexts_status.set_token(response.usage.total_tokens)
			self._request_prompt_tokens = response.usage.prompt_tokens

		if finish_reason == FinishReasons.TOOL_CALLING:

			if not isinstance(context, ToolCallingContext):
				raise IncompleteToolCallBlockError("tool_calls finish_reason 的消息格式无效")

			await self.on_tool_calling(context)
			return None

		if finish_reason in (FinishReasons.STOP, FinishReasons.LENGTH):
			if getattr(message, "tool_calls", None):
				raise IncompleteToolCallBlockError(f"finish_reason={finish_reason} 时 tool_calls 不完整")

			await self.on_context(context)

			if finish_reason == FinishReasons.LENGTH:
				logger.warning("模型输出因达到长度上限而截断")

			if self.is_generator_processing:
				self.set_stop_generator(True)

			return None

		raise UnknownFinishReasonError(f"未处理的finish_reason: {finish_reason}")

	async def on_stream_chunk(self, chunk: StreamChunk) -> Optional[AssistantOutput]:

		if not chunk.choices:
			return None

		choice = chunk.choices[0]
		self.stream_handler.merge(choice.delta)

		if choice.finish_reason is None:
			return None

		finish_reason	= choice.finish_reason
		handler			= self.stream_handler

		if finish_reason == FinishReasons.TOOL_CALLING:
			if not handler._tool_calls:
				raise IncompleteToolCallBlockError("tool_calls finish_reason 没有携带调用内容")

			await self.on_tool_calling(handler.build_tool_calling_context())
			handler.reset()

			return None

		if finish_reason in (FinishReasons.STOP, FinishReasons.LENGTH):
			if handler._tool_calls:
				raise IncompleteToolCallBlockError(f"finish_reason={finish_reason} 时 tool_calls 不完整")

			assistant_ctx = AssistantContext(content=handler._content, reasoning_content=handler._reasoning)
			await self.on_context(assistant_ctx)

			if finish_reason == FinishReasons.LENGTH:
				logger.warning("流式模型输出因达到长度上限而截断")

			if self.is_generator_processing:
				self.set_stop_generator(True)

			return handler.flush(finish_reason=finish_reason)

		raise UnknownFinishReasonError(f"未处理的finish_reason: {finish_reason}")

	async def on_build_output(self, response: Response) -> Optional[AssistantOutput]:
		return generate_assistant_output_by_response(response)

	async def on_stream_request(self) -> Union[AssistantOutput, None]:
		request = await self.on_build_request()
		contexts_status = self.assistant_session.contexts_status

		async for chunk in self.openai_client.call_stream(request=request):

			if self.is_stopping_generator:
				logger.info("流式请求被 stop 信号中断")
				return None

			if chunk.usage is not None:
				contexts_status.set_token(chunk.usage.total_tokens)
				self._request_prompt_tokens = chunk.usage.prompt_tokens

			if output := await self.on_stream_chunk(chunk):
				return output

		if self.stream_handler.is_empty:
			return None

		if self.stream_handler._tool_calls:
			raise IncompleteToolCallBlockError("流式连接在 tool call 完成前关闭")

		assistant_ctx = AssistantContext(
			content				= self.stream_handler._content,
			reasoning_content	= self.stream_handler._reasoning,
		)

		await self.on_context(assistant_ctx)

		if self.is_generator_processing:
			self.set_stop_generator(True)

		return self.stream_handler.flush()

	async def on_common_request(self) -> Union[AssistantOutput, None]:

		request		= await self.on_build_request()
		response	= await self.on_request(request)

		await self.on_response(response)
		return await self.on_build_output(response)

	async def on_round_initiate(self) -> None:

		if self.is_round_processing:
			raise GatewayBusyError("网关正在工作")

		self.set_processing(True)

		try:

			self._request_estimated_tokens	= None
			self._request_prompt_tokens		= None
			
			self.stream_handler.reset()

			if self.assistant_model_config.model_name != self.assistant_session.assistant_model_name:
				if not self.change_model(self.assistant_session.assistant_model_name):
					raise ModelConfigMissingError(f"找不到会话指定的模型: {self.assistant_session.assistant_model_name}")

			prompt_content = self.assistant_prompt.model_dump_json()
			current_prompt = self.assistant_session.contexts_status.prompt

			if current_prompt is None or current_prompt.content != prompt_content:
				self.assistant_session.contexts_status.set_prompt(SystemContext(content=prompt_content))

			await self.on_prepare_context_before_request()

			self._request_estimated_tokens = self.get_request_estimated_tokens()

		except Exception:
			self.set_processing(False)
			raise

	async def on_round_complete(self) -> None:
		
		if self.is_round_processing:
			self.set_processing(False)

		contexts_status	= self.assistant_session.contexts_status
		guessed			= self._request_estimated_tokens
		actual			= self._request_prompt_tokens

		if guessed is not None and actual is not None:
			
			self.token_tracker.calibrate_ratio(guessed=guessed, actual=actual)
			contexts_status.clear_tokens_cache()
			
			logger.info("估算 prompt tokens: %s", guessed)
			logger.info("实际 prompt tokens: %s", actual)
			logger.info("当前平均差值: %s", self.token_tracker.ratio)
		
		else:
			logger.info("本轮没有可用于校准的 prompt token usage")

		logger.info("实际 total tokens: %s", contexts_status.token)

	async def on_round_error(self, exception: Exception) -> None:
		
		"""处理可重试的网络或 API 错误，且不重置重试状态。"""
		
		if isinstance(exception, ResponseCodeError):
			code = exception.code

			if code == 429:
				delay = min(2 ** self._retry_count, 60)
				self._retry_count += 1
				logger.warning("限流 (429), %ss 后重试 (第%s次)", delay, self._retry_count)
				await asyncio.sleep(delay)
				return

			if code == 402:
				logger.error("余额不足 (402), 停止生成器")
				self.set_stop_generator(True)
				raise

			if code == 401:
				logger.warning("认证失败 (401), 尝试切换 key")
				current = self.keys_manager.get_available_key()
				if current:
					current.is_enable = False
				self.keys_manager.uncache_key()
				return

			if 500 <= code < 600:
				delay = min(2 ** self._retry_count, 30)
				self._retry_count += 1
				logger.warning("服务器错误 (%s), %ss 后重试",code, delay)
				await asyncio.sleep(delay)
				return

		if isinstance(exception, (asyncio.TimeoutError, aiohttp.ClientError)):
			delay = min(2 ** self._retry_count, 30)
			self._retry_count += 1
			logger.warning("网络错误: %s, %ss 后重试", exception, delay)
			await asyncio.sleep(delay)
			return

		logger.error("未处理的错误: %s: %s", type(exception).__name__, exception)
		self.set_stop_generator(True)
		raise exception

	async def on_generator_initiate(self) -> None:

		self.set_generator_start_timestamp(time.time())
		self.set_generator_complete_timestamp(None)
		self.set_generator_processing(True)
		self._retry_count = 0

	async def on_generator_end(self) -> None:

		self.set_generator_complete_timestamp(time.time())
		self.set_generator_processing(False)

	async def on_generator_error(self, exception: Exception) -> None:
		raise exception

	async def on_gateway_close(self) -> None:

		if (
			self._client_session is not None
			and not self._client_session.closed
		):
			await self._client_session.close()

	async def round_call(self) -> Union[AssistantOutput, None]:
		round_started = False

		try:

			await self.on_round_initiate()
			round_started = True

			if self.is_stopping_generator:
				return None

			if self.assistant_model_config.support_streaming:
				return await self.on_stream_request()

			return await self.on_common_request()

		except Exception as exception:
			await self.on_round_error(exception)

		finally:
			if round_started:
				await self.on_round_complete()

	async def async_generator(self) -> Iterator[AssistantOutput]:

		await self.on_generator_initiate()

		try:
			while True:

				if result := await self.round_call():
					yield result

				if self.is_stopping_generator:
					self.set_stop_generator(False)
					break

		except GeneratorExit:
			raise

		except Exception as exception:
			await self.on_generator_error(exception)

		finally:
			await self.on_generator_end()
