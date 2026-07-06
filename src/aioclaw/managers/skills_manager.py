from __future__ import annotations

from aioclaw.protocols	import SkillsManagerProtocol

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
	
	from aioclaw.models	import Skill


class SkillsManager(SkillsManagerProtocol):
	
	def __init__(self, skills: List[Skill]):
		
		# 建立引索表 实现O(1)查找
		self.skills = {skill.name: skill for skill in skills}
	
	def find(self, keywords: str) -> List[Skill]:
		
		"""这个应该叫做match(匹配才对)"""
		
		# 已经找到的
		found_skills = []
		
		for skill in self.skills.values():
			
			# 所有的关键词
			keyword_list = keywords.split(" ")
			
			is_found = any(
				keyword in skill.name or
				keyword in skill.description or
				keyword in skill.content
				for keyword in keyword_list
			)
			
			if is_found:
				found_skills.append(skill)
		
		return found_skills
	
	def add(self, skill: Skill) -> None:
		
		if skill.name not in self.skills:
		
			self.skills[skill.name] = skill
		
		return None
	
	def remove(self, skill: Skill) -> None:
		
		if skill.name in self.skills:
			
			self.skills.pop(skill.name)
		
		return None
	
	def get_by_name(self, skill_name: str) -> Skill | None:
		
		return self.skills.get(skill_name)