from enum	import Enum


class FileTypes(str, Enum):
	
	file		: str = "file"
	directory	: str = "directory"