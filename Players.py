# -*- coding: utf-8 -*-
"""
@author: Blopa
"""

import random
from Game import Player

class RandomPlayer(Player):
	def request_action(self):
		options = self.available_actions()
		all_options = []
		for action in options:
			possible_kwargs = options[action]
			for kwargs in possible_kwargs:
				all_options.append([action, kwargs])
		selection = random.choice(all_options)
		return selection[0],selection[1]
	
	def request_discard(self):
		return random.choice(self.cards).name