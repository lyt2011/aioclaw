from __future__ import annotations
from .base_gateway_error	import BaseGatewayError


class UnknownFinishReasonError(BaseGatewayError):
	
	"""未知/未处理的 finish_reason"""
	...