# -*- coding: utf-8 -*-
"""
@author: Blopa
Adaptation from: https://github.com/yawgmoth/PyPlanner/blob/master/pathfinding.py
"""

from Game import TurnPhase
import time

def default_heuristic(state):
    return 0

def default_mcts(state):
	return 0

def Astar(start_state, is_goal, heuristic=default_heuristic, mcts_evaluation=default_mcts, timeout = 20, expanded_limit=None, skipDraws=True):
	"""
	A* search algorithm. The function is passed a start State object, a heuristic function, and a goal predicate.
	
	The start state can produce neighbors as needed, see State.py for details.
	
	The heuristic is a function that takes one parameter: a neighbor structure tuple ((action,parameters),new_state,cost).
	The algorithm uses this heuristic to determine which node to expand next.
	
	The goal is a function that takes one parameter: a state, and returns True if that node is a goal state, otherwise False. 

	The function returns a 3-tuple (path,distance,counters):
		- path is a sequence of (action,parameter) tuples that have to be traversed to reach a goal state from the start
		- distance is the sum of costs of all edges in the path 
		- counters is a tuple consisting of (visited, expanded, duplicated, improved):
			-- visited: is the total number of nodes that were added to the frontier during the execution of the algorithm
			-- expanded: is the total number of nodes that were expanded during the execution of the algorithm 
			-- duplicated: is the total number of nodes that were equivalent to a previously visited node during the execution of the algorithm
			-- improved: is the total number of duplicated nodes that improved the previous discovered path
	"""
	if timeout is None:
		timeout = 115516800
	if expanded_limit is None:
		expanded_limit = 1401946112
	visited_cnt = 0
	expanded_cnt = 0
	duplicated_cnt = 0
	improved_cnt = 0
	visited = set()
	visited_goals = set()
	item = [start_state,0,0,[]]
	frontier = [item]
	frontier_dic = {start_state.id:item}
	minimum_found = 999999999
	default_path = []
	previous_goal = 0
	start_time = time.time()
	while frontier and (time.time()-start_time)<timeout and expanded_cnt<expanded_limit:
		current_state, current_dist, h, path = frontier[0]
		if is_goal(current_state):
			if not skipDraws or current_state.id in visited_goals or start_state.turn_phase==TurnPhase.DISCARD:
				return path,current_dist,(visited_cnt,expanded_cnt,duplicated_cnt,improved_cnt)
			else:
				draws_h = mcts_evaluation(current_state)
				item = frontier_dic[current_state.id]
				item[2] = h+draws_h
				if not visited_goals or item[2]<previous_goal:
					default_path = path
					previous_goal = item[2]
				visited_goals.add(current_state.id)
				frontier.sort(key=lambda x: x[1] + x[2])
				continue
		else:
			del frontier_dic[current_state.id]
			frontier = frontier[1:]
		neighbors = current_state.get_neighbors(skipDraws)
		visited.add(current_state.id)
		expanded_cnt += 1
		player_plan = current_state.current_player == start_state.current_player
		for neighbor in neighbors:
			new_state = neighbor[1]
			nid = new_state.id
			new_path = (path + [neighbor[0]]) if player_plan else (path)
			if nid not in visited:
				visited_cnt += 1
				h = heuristic(new_state)
				cost = current_dist+neighbor[2]
				old_cost = 0
				item = frontier_dic.get(nid)
				if item is not None:
					old_cost = item[1] + item[2]
					duplicated_cnt += 1
					if old_cost > cost + h:
						item[0],item[1],item[2],item[3] = new_state,cost,h,new_path
						improved_cnt += 1
				else:
					item = [new_state,cost,h,new_path]
					frontier.append(item)
					frontier_dic[new_state.id] = item
				if (cost + h)<minimum_found:
						minimum_found = cost + h
		if frontier and minimum_found <= (frontier[0][1]+frontier[0][2]):
			frontier.sort(key=lambda x: x[1] + x[2])
			minimum_found = 9999999999
		if frontier and not visited_goals and len(frontier[0][3])>len(default_path):
			_,_,_,default_path = frontier[0]
#	print("Expanded: %i  Visited: %i  Frontier: %i Total-t: %.2f" % (expanded_cnt,visited_cnt,len(frontier),time.time()-start_time))
	return default_path,None,(visited_cnt,expanded_cnt,duplicated_cnt,improved_cnt)
	
if __name__ == '__main__':
	from Game import Game, Player
	from Heuristics import Heuristic
	from Players import PlanningPlayer
	game = Game([Player(),Player()])
	
	def goal_test_movement(state):
		return any([p.position=="karachi" for p in state.players])
	
	def goal_test_curing(state):
		return all(state.cures.values())
	
	tests = 10
	total_time = 0
	total_visited = 0
	total_expanded = 0
	total_duplicated = 0
	total_improved = 0
	for i in range(tests):
		game.setup(seed=1337*(i+1))
		state = game.copy()
		t_start = time.time()
#		print(game.players)
#		print(game.players[0].colors,game.players[1].colors)
		custom_heuristic,_ = PlanningPlayer.goal_heuristic_chooser(state)
		path,distance,counters = Astar(state,custom_heuristic,goal_test_curing,timeout=None,expanded_limit=3500,skipDraws=False)
		visited,expanded,duplicated,improved = counters
		t_taken = time.time() - t_start
		print("Plan:",path)
		print("Time taken:",t_taken)
		print("Distance:",distance)
		print("Number of visited nodes:",visited)
		print("Number of expanded nodes:",expanded)
		print("Number of duplicated nodes:",duplicated)
		print("Number of improved nodes:",improved)
		total_time += t_taken
		total_visited += visited
		total_expanded += expanded
		total_duplicated += duplicated
		total_improved += improved
	print("Average time taken:",total_time/tests)
	print("Average visited nodes:",total_visited/tests)
	print("Average expanded nodes:",total_expanded/tests)
	print("Average duplicated nodes:",total_duplicated/tests)
	print("Average improved nodes:",total_improved/tests)