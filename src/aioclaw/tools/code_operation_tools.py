from ..protocols	import ToolSetProtocol, ToolsManagerProtocol

from aioverse.utils.syntax_sugar import build_tool_schema

from io			import StringIO
from contextlib	import redirect_stdout, redirect_stderr
from asyncio	import create_subprocess_shell

import asyncio
import traceback


# py代码运行
PythonRunnerSchema = build_tool_schema(
	tool_name			= "python_runner",
	tool_description	= "运行python代码",
	requirements		= ["code"],
	arguments			= {
		"code"			: ("string", "需要运行的代码"),
		"timeout"		: ("integer", "运行超时 单位为秒", 10),
		"output_limit"	: ("integer", "输出长度限制 超过则后续部分使用'...'截断", 800)
	}
)

# bash指令运行
BashRunnerSchema = build_tool_schema(
	tool_name			= "bash_runner",
	tool_description	= "运行bash指令，支持管道",
	requirements		= ["command"],
	arguments			= {
		"command"		: ("string", "需要运行的指令"),
		"timeout"		: ("integer", "运行超时 单位为秒", 10),
		"work_directory": (["string", "null"], "工作目录 默认为当前目录", None),
		"output_limit"	: ("integer", "输出长度限制 超过则后续部分使用'...'截断", 800)
	}
)


class CodeOperationTools(ToolSetProtocol):
	
	def __init__(self, *args, **kwargs):
		
		super().__init__(*args, **kwargs)
	
	def register(self, tools_manager: ToolsManagerProtocol):
		
		super().register(tools_manager)
		
		tools_manager.register(self.python_runner, PythonRunnerSchema)
		tools_manager.register(self.bash_runner, BashRunnerSchema)
		
		return None
	
	async def python_runner(
		self,
		code		: str,
		timeout		: int = 10,
		output_limit: int = 800
	) -> str:
	
		code_buffer = StringIO()
		
		def _runner(code: str) -> str:
		
			with redirect_stdout(code_buffer), redirect_stderr(code_buffer):
				
				try				: exec(code)
				except Exception: traceback.print_exc() # 错误信息打印到stderr
		
			return None
		
		coro = asyncio.to_thread(_runner, code)
		
		try:
			
			await asyncio.wait_for(coro, timeout=timeout)	
		
		# 仅捕获代码超时
		except asyncio.TimeoutError:
			
			code_buffer.write("代码运行超时")
		
		output = code_buffer.getvalue()
		
		return (
			f"{output[:output_limit]}" if len(output) > output_limit
			else output
		)
	
	async def bash_runner(
		self,
		command			: str,
		timeout			: int = 10,
		work_directory	: str | None = None,
		output_limit	: int = 800
	) -> str:
		
		"""居然有异步执行器😋😋😋"""
		
		proc = await create_subprocess_shell(
			cmd		= command,
			cwd		= work_directory,
			stdout	= asyncio.subprocess.PIPE,
			stderr	= asyncio.subprocess.STDOUT
		)
		
		try:
			
			output, _ = await asyncio.wait_for(
				proc.communicate(),
				timeout	= timeout
			)
			output	= output.decode()
		
		except asyncio.TimeoutError:
			
			output = "代码执行超时"
		
		finally:
			
			if proc.returncode is None:
				
				proc.kill()
				await proc.wait()
				
		# 对输出进行裁剪
		return f"{output[:output_limit]}..." if len(output) > output_limit else output