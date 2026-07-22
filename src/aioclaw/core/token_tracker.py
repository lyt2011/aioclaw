from __future__ import annotations

from tiktoken		import encoding_for_model
from collections	import deque
from typing			import List


class TokenTracker:

	def __init__(
		self,
		default_model		: str	= "gpt-4o",
		calibration_percent	: float	= 1.05,
		window_length		: int	= 15 # 测试得出最佳值 ~15
	):

		self._enc	= encoding_for_model(default_model)

		self._ratios				= deque(maxlen=window_length)
		self._calibration_percent	= calibration_percent


	@property
	def ratio(self) -> float:

		"""返回 historical actual/guessed 的平均比值，无数据时返回 1.0（中性）"""

		if not self._ratios:
			return 1.0

		ratio = sum(self._ratios) / len(self._ratios)

		return ratio if ratio > 0 else 1.0 # 确保返回非0

	
	def calibrate_ratio(self, guessed: int, actual: int):

		"""记录 actual/guessed 比值，用于比例校准"""

		if guessed > 0 and actual > 0:
			self._ratios.append(actual / guessed)


	def _get_tokens_by_tiktoken(self, contents: List[str]) -> int:

		"""通过 tiktoken 估算 tokens"""

		tokens = (len(self._enc.encode(c, disallowed_special=())) for c in contents)
		return sum(tokens)

	def estimate(self, contents: List[str]) -> int:

		guess_token = self._get_tokens_by_tiktoken(contents)	# 原始估算
		guess_token = guess_token * self._calibration_percent	# 保守偏大系数
		guess_token = guess_token * self.ratio					# 比例校准（替代差值）

		return int(max(guess_token, 0)) # 确保返回自然数


# 全局单例
token_tracker = TokenTracker()
