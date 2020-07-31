# -*- coding: utf-8 -*-
"""
@author: Blopa
"""

import random
from functools import partial
from Game import Player,PlayerRole
from Heuristics import Heuristic
from Pathfinding import Astar
from MCTSModeling import MCTSModeling

class RandomPlayer(Player):
	def request_action(self,game):
		options = self.available_actions(game)
		all_options = []
		for action in options:
			possible_kwargs = options[action]
			for kwargs in possible_kwargs:
				all_options.append([action, kwargs])
		selection = random.choice(all_options)
		return selection[0],selection[1]
	
	def request_discard(self,game):
		return random.choice(self.cards).name

class HeuristicPlayer(Player):
	def request_action(self,game):
		state = game.copy(randomize=False,skipDraws=False)
		neighbors = state.get_neighbors(skipDraws=True)
		minimum = None
		best = [None,None]
		for neighbor in neighbors:
			h = Heuristic.heuristic(neighbor[1],True,True)
			if minimum is None or h<minimum:
				minimum = h
				best = neighbor[0]
		return best[0],best[1]
	
	def request_discard(self,game):
		state = game.copy(randomize=False,skipDraws=False)
		neighbors = state.get_neighbors(skipDraws=True)
		minimum = None
		best = [None,None]
		for neighbor in neighbors:
			h = Heuristic.heuristic(neighbor[1],True,True)
			if minimum is None or h<minimum:
				minimum = h
				best = neighbor[0]
		return best[1]['discard']

class PlanningPlayer(Player):
	def __init__(self):
		super().__init__()
		self.last_planning = -1
		self.last_planning_phase = None
		self.plan = []
		self.my_plan_name = None
	
	# Goals	
	@staticmethod
	def goal_get_2_next(game,turn):
		return game.current_turn == turn
	
	@staticmethod
	def goal_discover_cure(game,n_cures):
		return sum(game.cures.values())==n_cures

	@classmethod
	def goal_heuristic_chooser(cls,game):
		player = game.players[game.current_player]
		required = 4 + (player.playerrole!=PlayerRole.SCIENTIST)
		discoverCure = False
		for color in player.colors:
			if player.colors[color]>=required:
				discoverCure = True
				break
			elif player.colors[color]==required-1:
				for p in game.players:
					if player != p and p.colors[color]>0 and game.distances[p.position][player.position]<=4:
						for card in p.cards:
							if card.color==color and (card.name==p.position or p.playerrole==PlayerRole.RESEARCHER):
								discoverCure = True
			elif player.colors[color]>0:
				for p in game.players:
					if player != p and p.colors[color]==3+(p.playerrole!=PlayerRole.SCIENTIST) and game.distances[p.position][player.position]<=4:
						for card in player.cards:
							if card.color==color and (card.name==p.position or player.playerrole==PlayerRole.RESEARCHER):
								discoverCure = True

		if discoverCure:
			return (partial(Heuristic.heuristic,find_rs=True), partial(cls.goal_discover_cure,n_cures=sum(game.cures.values())+1),"discover_cure")
		else:
			return (partial(Heuristic.heuristic,find_diseases=True),partial(cls.goal_get_2_next,turn=game.current_turn+2),"survive")
	
	def get_plan_step(self,game):
		if not self.plan or self.last_planning!=game.current_turn or self.last_planning_phase!=game.turn_phase:
			initial_state = game.copy(randomize=True)
			mcts = MCTSModeling(initial_state=initial_state,rollouts=100)
			my_heuristic,my_goal,self.my_plan_name = PlanningPlayer.goal_heuristic_chooser(initial_state)
			self.plan,_,_ = Astar(initial_state,heuristic=my_heuristic,is_goal=my_goal,mcts_evaluation=mcts.predict,timeout=None,expanded_limit=3500,skipDraws=True)
			self.last_planning = game.current_turn
			self.last_planning_phase = game.turn_phase
		if not self.plan:
			print("Error making plan")
			return None
		step = self.plan.pop(0)
		return step[0],step[1]
	
	def request_action(self,game):
		return self.get_plan_step(game)
			
	def request_discard(self,game):
		if self.plan and self.plan[0][0] != self.discard.__name__:
			self.plan = []
		_, params = self.get_plan_step(game)
		return params['discard']
