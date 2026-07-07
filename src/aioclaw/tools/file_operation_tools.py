from ..protocols	import ToolSetProtocol, ToolsManagerProtocol

from aioverse.utils.syntax_sugar import build_tool_schema

from typing		import Optional

import aiofiles
import os
import shutil
import orjson
import asyncstdlib


# 写文件
WriteFileSchema = build_tool_schema(
	tool_name			= "write_file",
	tool_description	= "将内容写入到文件",
	requirements		= ["file_path", "content"],
	arguments			= {
		"file_path"	: ("string", "文件路径"),
		"content"	: ("string", "具体写入内容"),
		"encoding"	: ("string", "编码方式", "utf-8"),
		"mode"		: ("string", "写入模式 w代表覆盖 a代表追加", "w")
	}
)

# 复制文件
CopyFileSchema = build_tool_schema(
	tool_name			= "copy_full_file",
	tool_description	= "复制完整文件",
	requirements		= ["file_path", "target_path"],
	arguments			= {
		"file_path": ("string", "待复制文件的路径"),
		"target_path": ("string", "目标文件或路径")
	}
)

# 改变文件行内容
ChangeFileLineSchema = build_tool_schema(
	tool_name			= "change_file_line",
	tool_description	= "修改文件某行的数据",
	requirements		= ["file_path", "new_data", "line", ],
	arguments			= {
		"file_path"		: ("string", "文件路径"),
		"line"			: ("integer", "目标行"),
		"new_data"		: ("string", "新的行数据"),
		"source_data"	: (["string", "null"], "行原数据 传入则验证两者是否相同", None),
		"encoding"		: ("string", "编码方式", "utf-8")
	}
)

# 删除文件
DeleteFileSchema = build_tool_schema(
	tool_name			= "delete_file",
	tool_description	= "删除一个文件",
	requirements		= ["file_path"],
	arguments			= {
		"file_path": ("string", "目标文件路径")
	}
)

# 搜索目录内容
ScanDirectorySchema = build_tool_schema(
	tool_name			= "scan_directory",
	tool_description	= "获取单个文件夹里面的文件/文件夹",
	requirements		= ["directory_path"],
	arguments			= {
		"directory_path": ("string", "目标文件夹路径")
	}
)

# 在文件里面找东西
FindInFileSchema = build_tool_schema(
	tool_name			= "find_in_file",
	tool_description	= "在文件中查找带有关键词的行",
	requirements		= ["file_path", "keywords"],
	arguments			= {
		"file_path"	: ("string", "文件路径"),
		"keywords"	: ("string", "关键词组 使用空格分割"),
		"encoding"	: ("string", "编码方式", "utf-8")
	}
)

# 创建目录
CreateDirectorySchema = build_tool_schema(
	tool_name			= "create_directory",
	tool_description	= "创建一个目录 如果父目录不存在也会一并创建",
	requirements		= ["directory_path"],
	arguments			= {
		"directory_path": ("string", "要创建的目录路径 支持多级目录 使用/分割 如: a/b/c")
	}
)

# 根据行读文件
ReadFileLinesSchema = build_tool_schema(
	tool_name			= "read_file_lines",
	tool_description	= "从文件的某一行开始读取",
	requirements		= ["file_path", "lines_count"],
	arguments			= {
		"file_path"		: ("string", "目标文件路径"),
		"lines_count"	: ("integer", "需要读取的行数量 -1表示读取到文件末尾", -1),
		"offset_lines"	: ("integer", "行偏移量 表示从第n行开始 默认第一行", 1),
		"encoding"		: ("string", "编码方式", "utf-8")
	}
)

# 完全读取一个文件
ReadFileSchema = build_tool_schema(
	tool_name			= "read_file",
	tool_description	= "读取一个文件",
	requirements		= ["file_path"],
	arguments			= {
		"file_path"		: ("string", "目标文件路径"),
		"encoding"		: ("string", "编码方式", "utf-8")
	}
)


# 文件操作类
class FileOperationTools(ToolSetProtocol):
	
	def __init__(self, *args, **kwargs):
		
		super().__init__(*args, **kwargs)
	
	def register(self, tools_manager: ToolsManagerProtocol):
		
		super().register(tools_manager)
	
		tools_manager.register(self.write_file, WriteFileSchema)
		tools_manager.register(self.copy_full_file, CopyFileSchema)
		tools_manager.register(self.change_file_line, ChangeFileLineSchema)
		tools_manager.register(self.delete_file, DeleteFileSchema)
		tools_manager.register(self.scan_directory, ScanDirectorySchema)
		tools_manager.register(self.find_in_file, FindInFileSchema)
		tools_manager.register(self.create_directory, CreateDirectorySchema)
		tools_manager.register(self.read_file_lines, ReadFileLinesSchema)
		tools_manager.register(self.read_file, ReadFileSchema)
	
	async def read_file_lines(
		self,
		file_path	: str,
		lines_count	: int = -1, # -1读到文件末尾
		offset_lines: int = 1,
		**kwargs
	) -> str:
		
		"""按行读取文件"""
		
		current_line = 1
		readed_lines = []
		
		if not os.path.isfile(file_path): return f"{file_path} 不存在"
		
		async with aiofiles.open(file_path, **kwargs) as file:
		
			async for line in file:
				
				# 优化性能 不等于-1才计算已读取的长度
				if lines_count != -1 and len(readed_lines) == lines_count: break
				
				if current_line >= offset_lines: readed_lines.append(line)
				
				current_line += 1
		
		return "\n".join(readed_lines)
	
	async def read_file(
		self,
		file_path	: str,
		encoding	: str = "utf-8"
	) -> str:
		
		if not os.path.isfile(file_path): return f"{file_path} 不存在"
		
		async with aiofiles.open(file_path, encoding=encoding) as file:
			
			content = await file.read()
		
		return content
	
	async def write_file(
		self,
		file_path	: str,
		content		: str,
		mode		: str = "w",
		**kwargs
	) -> str:
		
		"""写入文件"""
		
		# 限制模式
		if mode not in ("w", "a"):
			return f"不支持 {mode} 模式"
		
		# 默认用w是因为content只能为字符串 而字符串不能写入二进制 支持wb也没用
		async with aiofiles.open(file_path, mode, **kwargs) as file:
			write_length = await file.write(content)
		
		return (
			f"{file_path} 写入完成 "
			f"输入字符数: {len(content)} "
			f"写入字符数: {write_length}"
		)
		
	async def change_file_line(
		self,
		file_path	: str,
		line		: int,
		new_data	: str,
		source_data	: Optional[str] = None,
		encoding	: str = "utf-8"
	) -> str:
		
		"""修改文件某行数据"""
		
		if not os.path.isfile(file_path):
			return f"{file_path} 不存在"
		if line <= 0:
			return "行数必须大于0"
		
		# 先获取文件内容
		async with aiofiles.open(
			file_path,
			"r",
			encoding=encoding
		) as file:
			
			file_content = await file.read()
		
		# 对文件通过\n分割每一行
		file_lines			= file_content.split("\n")
		file_lines_length	= len(file_lines)
		line_index			= line - 1
		
		if line > file_lines_length:
			return f"行数({line})不可大于文件总行数({file_lines_length})"
		
		# 对原行进行备份
		source_data_backup	= file_lines[line_index]
		
		# 若source_data传入 对其验证
		if source_data and source_data_backup != source_data:
			return f"原行数据与目标行数据不一致"
		
		# 更改该行数据
		file_lines[line_index] = new_data.replace("\n", "") # 防止换行符注入
		
		# 再通过\n连接并写入回去
		async with aiofiles.open(
			file_path,
			"w",
			encoding=encoding
		) as file:
			
			await file.write("\n".join(file_lines))
		
		return f"修改成功: {source_data_backup} -> {new_data}"
	
	def copy_full_file(
		self,
		file_path	: str,
		target_path	: str
	) -> str:
		
		"""复制一整个文件"""
		
		if not os.path.exists(file_path):
			return f"{file_path} 不存在"
		
		shutil.copy(file_path, target_path)
		
		return (
			f"复制完成 ({file_path} -> {target_path}) "
			f"{file_path} 大小: {os.path.getsize(file_path)} bytes "
			f"{target_path} 大小: {os.path.getsize(target_path)} bytes"
		)
	
	def delete_file(
		self,
		file_path: str
	) -> str:
		
		"""删除文件"""
		
		if not os.path.exists(file_path):
			return f"{file_path} 不存在"
		
		os.remove(file_path)
		
		return f"{file_path} 删除成功"
	
	def scan_directory(
		self,
		directory_path	: str,
		link_char		: str = ","
	) -> str:
		
		if not os.path.isdir(directory_path):
			
			return f"{directory_path} 不存在"
		
		files = os.listdir(directory_path)
		
		return (
			link_char.join(files) if files
			else f"该文件夹没有任何文件"
		)
	
	def create_directory(
		self,
		directory_path: str
	) -> str:
		
		directory_path = directory_path.replace("/", os.sep)
		
		if os.path.isdir(directory_path): return f"{directory_path} 目录已存在"
		
		os.makedirs(directory_path, exist_ok=True)
		
		return f"{directory_path} 目录创建完成"
	
	async def find_in_file(
		self,
		file_path	: str,
		keywords	: str,
		encoding	: str = "utf-8"
	) -> str:
		
		if not os.path.isfile(file_path): return f"{file_path} 不存在"
		
		if not (keywords := keywords.strip()): return f"至少需要一个关键词"
		
		# 分割关键词
		keywords = keywords.split(" ")
		
		async with aiofiles.open(file_path, "r", encoding=encoding) as file:
				
			found_lines = {
				f"Line {index}": line
				async for index, line in asyncstdlib.enumerate(file, start=1)
				if any(keyword in line for keyword in keywords)
			}
		
		return orjson.dumps(found_lines).decode()