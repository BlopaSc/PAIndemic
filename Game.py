# -*- coding: utf-8 -*-
"""
@author: Blopa
"""

import copy
import functools
import itertools
import numpy as np
import random
import sys
import traceback
from enum import IntEnum, auto
from city_cards import city_cards


def empty_function(self,*args):
	return

class CardType(IntEnum):
	MISSING = auto()
	CITY = auto()
	EVENT = auto()
	EPIDEMIC = auto()

class PlayerRole(IntEnum):
	NULL = auto()
	CONTINGENCY_PLANNER = auto()
	DISPATCHER = auto()
	MEDIC = auto()
	OPERATIONS_EXPERT = auto()
	QUARANTINE_SPECIALIST = auto()
	RESEARCHER = auto()
	SCIENTIST = auto()

class GameState(IntEnum):
	NOT_PLAYING = auto()
	PLAYING = auto()
	LOST = auto()
	WON = auto()

class TurnPhase(IntEnum):
	INACTIVE = auto()
	NEW = auto()
	ACTIONS = auto()
	DRAW = auto()
	DISCARD = auto()
	INFECT = auto()


class Game:
	### String representation of the game, prints basic state information
	def __repr__(self):
		s = "Turn: "+str(self.current_turn)+", Current player: "+str(self.players[self.current_player].playerrole.name)+", Out.Counter: "+str(self.outbreak_counter)+", Inf.Counter: "+str(self.infection_counter)+", Inf.Rate: "+str(self.infection_rate)+"\n"
		s+= "Cures found: "+str([color+"="+str((2 if self.eradicated[color] else 1) if self.cures[color] else 0) for color in self.commons['colors']])+"\n"
		for p,player in enumerate(self.players):
			s += "Player "+str(p)+": "+str(player)+"\n"
		s+="Cities:\n"
		for city in self.cities:
			if self.cities[city].research_station or any([self.cities[city].disease_cubes[color]>0 for color in self.commons['colors']]):
				s += str(self.cities[city])+"\n"
		s+="Player deck: "+str(self.player_deck)+"\n"
		s+="Infection deck: "+str(self.infection_deck)
		return s
	### Returns dictionary of current game state, clears current game_log as to only have changes
	def __call__(self):
		game = {
			'game_state': self.game_state.name,
			'game_turn': self.current_turn,
			'turn_phase': self.turn_phase.name,
			'current_player': self.current_player,
			'infections': self.infection_counter,
			'infection_rate': self.infection_rate,
			'outbreaks': self.outbreak_counter,
			'cures': self.cures,
			'eradicated': self.eradicated,
			'disease_cubes': self.remaining_disease_cubes,
			'players': {"p"+str(p): self.players[p]() for p in range(len(self.players))},
			'cities': {city: self.cities[city]() for city in self.cities},
			'quarantine_cities': self.protected_cities,
			'infection_deck': self.infection_deck(),
			'player_deck': self.player_deck(),
			'actions': self.players[self.current_player].available_actions(self),
			'remaining_actions': self.actions,
			'game_log': self.commons['game_log']
		}
		self.commons['game_log'] = ""
		return game
	### Constructor function, players is a list of Player-objects, the number of players is defined by the number of objects in the list
	def __init__(self,players,epidemic_cards=4,cities=city_cards,starting_city="atlanta",number_cubes=24,log_game=True,external_log=None):
		assert(starting_city in cities)
		# Save game parameters
		self.commons = {}
		self.commons['epidemic_cards'] = epidemic_cards
		self.commons['starting_city'] = starting_city
		self.commons['number_cubes'] = number_cubes
		self.commons['colors'] = []
		# Logger/external log: if not None then saves text record of game
		self.commons['logger'] = external_log
		# Log game: if True will save the text record of the game in commons[game_log]
		self.commons['log_game'] = log_game
		self.commons['game_log'] = ""
		# Record: for each game turn saves a list of tuples-actions: (game_state, current_player, action_name, parameters)
		self.commons['record'] = {}
		# Flag to record previous player actions and states
		self.record_actions = True
		# Gather city colors and disease cubes
		for city in city_cards:
			if city_cards[city]['color'] not in self.commons['colors']:
				self.commons['colors'].append(city_cards[city]['color'])
		# Save players
		self.players = players
		# Create cities
		self.cities = {city: City(name=city,color=city_cards[city]['color'],neighbors=city_cards[city]['connects'],colors=self.commons['colors']) for city in city_cards}
		# Create decks
		# TODO: Include events?
		cities_deck = [Card(name=city,cardtype=CardType.CITY,color=self.cities[city].color) for city in self.cities]
		event_deck = []
		self.infection_deck = InfectionDeck(cities_deck)
		cities_deck.extend(event_deck)
		self.player_deck = PlayerDeck(cities_deck)
		self.actions = 0
		# Calculate max turns
		self.commons['max_turns'] = 1 + ((len(cities_deck)+epidemic_cards-((6-len(self.players))*len(self.players)))//2)
		# Create PRNG
		self.prng = random.Random()
		# Turn controls
		self.current_player = -1
		self.current_turn = -1
		self.turn_phase = TurnPhase.INACTIVE
		self.game_state = GameState.NOT_PLAYING
		self.id = None
	### Compares the id of two Game-objects
	def __eq__(self,other):
		return self.id == other.id
	### Returns a tuple-id of the game, might be different from game-id and changes after each action/phase
	def get_id(self):
		# Everything not included can be derived from other data
		return (
				self.game_state, 
				self.current_turn, 
				self.turn_phase,
				self.infection_counter,
				self.outbreak_counter,
				tuple(self.cures.values()),
				tuple(self.eradicated.values()),
				tuple(self.remaining_disease_cubes.values()),
				tuple(p.get_id() for p in self.players),
				tuple(c.get_id() for c in self.cities.values()),
				self.actions
		  )
	### Returns an independent copy of the current game, might randomize the decks to equally valid possible states	
	def copy(self,randomize=True,skipDraws=False):
		game = copy.copy(self)
		game.log = functools.partial(empty_function,game)
		game.record_actions = False
		game.prng = random.Random()
		game.prng.setstate(self.prng.getstate())
		if randomize:
			game.player_deck = copy.copy(self.player_deck)
			game.infection_deck = copy.copy(self.infection_deck)
			game.player_deck.deck = self.player_deck.get_possible_deck(game.prng)
			game.infection_deck.deck = self.infection_deck.get_possible_deck(game.prng)
		# Advance to a decision making point
		if skipDraws:
			if game.turn_phase == TurnPhase.DRAW or game.turn_phase == TurnPhase.INFECT:
				game.turn_phase = TurnPhase.NEW
		game.game_advance()
		game.id = hash(game.get_id())
		return game
	### Returns a list of all possible valid next states of the game (requires the current state turn phase to be ACTIONS or DISCARD)
	def get_neighbors(self,skipDraws=False):
		result = []
		player = self.players[self.current_player]
		options = player.available_actions(self) if self.turn_phase == TurnPhase.ACTIONS or self.turn_phase == TurnPhase.DISCARD else []
		cost = 1 if self.turn_phase == TurnPhase.ACTIONS else (2 if self.turn_phase == TurnPhase.DISCARD else 0)
		for action in options:
			for parameters in options[action]:
				new_game = copy.copy(self)
				if self.turn_phase == TurnPhase.ACTIONS:
					new_game.do_action(action,parameters)
				elif self.turn_phase == TurnPhase.DISCARD:
					new_game.do_discard(**parameters)
				if new_game.turn_phase == TurnPhase.DRAW:
					if skipDraws:
						new_game.turn_phase = TurnPhase.INFECT
					else:
						new_game.draw_phase()
				if new_game.turn_phase == TurnPhase.INFECT:
					if skipDraws:
						new_game.current_player = (new_game.current_player+1)%len(new_game.players)
						new_game.current_turn += 1
						new_game.turn_phase = TurnPhase.NEW
					else:
						new_game.end_turn()
				if new_game.turn_phase == TurnPhase.NEW:
					new_game.start_turn()
				new_game.id = hash(new_game.get_id())
				result.append(((action,parameters),new_game,cost))
		return result
	### Log function: writes to game_log if it was requested and to logger if a stream was provided
	def log(self,new_log):
		if self.commons['log_game']:
			self.commons['game_log'] += new_log+"\n"
		if self.commons['logger'] is not None:
			self.commons['logger'].write(new_log+"\n")
			self.commons['logger'].flush()
	### Loads from a log file (automatically written using the log function), the Constructor settings must be the same for both games
	def load_from_log(self,filename):
		with open(filename,'r') as file:
			players_roles,seed = None,None
			lines = file.readlines()
			for l,line in enumerate(lines):
				line=line[:-1]
				if line.startswith("Seed"):
					seed = int(line[line.find('=')+1:])
				elif line.startswith("Roles"):
					roles = {role.name: role for role in list(PlayerRole)}
					players_roles = [roles[name] for name in line[line.find('=')+1:].split(',')]
				elif line.startswith("Setting game up"):
					self.setup(players_roles,seed)
					players_roles,seed = None,None
				elif line.find("discarded")!=-1:
					if self.turn_phase == TurnPhase.DISCARD:
						self.do_discard(line[line.find(':')+2:])
				elif line.find("drove")!=-1:
					self.do_action(Player.drive_ferry.__name__,{"target":line[line.find(':')+2:]})
				elif line.find("direct flew")!=-1:
					self.do_action(Player.direct_flight.__name__,{"target":line[line.find(':')+2:]})
				elif line.find("charter flew")!=-1:
					self.do_action(Player.charter_flight.__name__,{"target":line[line.find(':')+2:]})
				elif line.find("shuttle flew")!=-1:
					self.do_action(Player.shuttle_flight.__name__,{"target":line[line.find(':')+2:]})
				elif line.find("built research station")!=-1:
					replace = lines[l+1][lines[l+1].find(':')+2:-1] if (l+1)<len(lines) and lines[l+1].find("removed research station")!=-1 else 'none'
					self.do_action(Player.build_researchstation.__name__,{'replace':replace})
				elif line.find("treated")!=-1:
					self.do_action(Player.treat_disease.__name__,{"color":line[line.find(':')+2:]})
				elif line.find("gave")!=-1:
					pid = -1
					for p in self.players:
						if p.playerrole.name == line[line.find(':')+2:]:
							pid = p.pid
					self.do_action(Player.give_knowledge.__name__,{'receiver':pid,'target':line[line.find("gave")+5:line.find(" to: ")]})
				elif line.find("received")!=-1:
					pid = -1
					for p in self.players:
						if p.playerrole.name == line[line.find(':')+2:]:
							pid = p.pid
					self.do_action(Player.receive_knowledge.__name__,{'giver':pid,'target':line[line.find("received")+9:line.find(" from: ")]})
				elif line.find("discovered cure")!=-1:
					cards = []
					for i in range(1,6 - (self.players[self.current_player].playerrole==PlayerRole.SCIENTIST)):
						if lines[l+i].find("discarded")!=-1:
							cards.append(lines[l+i][lines[l+i].find(':')+2:-1])
					self.do_action(Player.discover_cure.__name__,{'color':line[line.find(':')+2:], 'chosen_cards':cards})
				# TODO: Implement other possible actions: rally, special charter flight
				self.game_advance()
	### Setup function: Allows specifying the player roles (as a list) and the randomness seed for the game
		### MUST be called before starting a game
	def setup(self,players_roles=None,seed=None):
		self.commons['game_log'] = ""
		if players_roles is not None:
			txt="Roles="
			for role in players_roles:
				txt+=role.name+","
			self.log(txt[:-1])
		if seed is not None:
			self.prng.seed(seed)
			self.log("Seed="+str(seed))
		self.log("Setting game up")
		if players_roles is None or len(players_roles)!=len(self.players):
			roles = list(PlayerRole)
			roles.remove(PlayerRole.NULL)
			# TODO: DISPATCHER and CONTINGENCY_PLANNER NOT FULLY IMPLEMENTED
			roles.remove(PlayerRole.CONTINGENCY_PLANNER)
			roles.remove(PlayerRole.DISPATCHER)
			# REMOVED OPERATIONS_EXPERT BECAUSE OF SEARCH SPACE EXPLOSION
			roles.remove(PlayerRole.OPERATIONS_EXPERT)
			players_roles = self.prng.sample(roles,len(self.players))
		# Player setup
		for p,player in enumerate(self.players):
			player.pid = p
			player.position = self.commons['starting_city']
			player.playerrole = players_roles[p]
			if player.playerrole == PlayerRole.OPERATIONS_EXPERT:
				player.special_move = False
			self.player_deck.discard.extend(player.cards)
			player.cards = []
			player.colors = {color:0 for color in self.commons['colors']}
		# City setup
		for c in self.cities:
			city = self.cities[c]
			# Restarts disease cubes and research station flag
			for color in city.disease_cubes:
				city.disease_cubes[color] = 0
			city.research_station = False
		self.cities[self.commons['starting_city']].research_station = True
		self.cities_rs = [self.commons['starting_city']]
		self.distances = {}
		self.calculate_distances()
		# Set counters
		self.remaining_disease_cubes = {color: self.commons['number_cubes'] for color in self.commons['colors']}
		self.cures = {color: False for color in self.commons['colors']}
		self.eradicated = {color: False for color in self.commons['colors']}
		self.outbreak_counter = 0
		self.infection_counter = 0
		self.infection_rate = 2
		self.research_station_counter = 1
		self.protected_cities = []
		self.medic_position = None
		# Prepare player deck
		# Removes epidemic cards
		self.player_deck.deck = [card for pile in self.player_deck.deck for card in pile if card.cardtype != CardType.EPIDEMIC]
		self.player_deck.deck.extend(self.player_deck.discard)
		self.player_deck.deck.sort(key = lambda x: str(x))
		self.player_deck.discard = []
		self.prng.shuffle(self.player_deck.deck)
		# Deal players' hands
		for player in self.players:
			for c in range(6-len(self.players)):
				card = self.player_deck.deck.pop()
				self.log(player.playerrole.name+" drew: "+card.name)
				player.cards.append(card)
				player.colors[card.color]+=1
		# Define starting player
		maximum_population = 0
		starting_player = 0
		for p, player in enumerate(self.players):
			current_population = max([city_cards[card.name]['pop'] if card.cardtype==CardType.CITY else 0 for card in player.cards])
			if current_population >= maximum_population:
				starting_player = p
				maximum_population = current_population
		# Setup player deck
		subpiles = [[Card(name="Epidemic",cardtype=CardType.EPIDEMIC,color="epidemic")] for i in range(self.commons['epidemic_cards'])]
		for index,card in enumerate(self.player_deck.deck):
			subpiles[index%self.commons['epidemic_cards']].append(card)
		self.player_deck.deck = []
		for pile in subpiles:
			self.prng.shuffle(pile)
			self.player_deck.deck.append(pile)
		self.player_deck.remaining = sum(len(p) for p in self.player_deck.deck)
		self.player_deck.expecting_epidemic = True
		self.player_deck.epidemic_countdown = len(self.player_deck.deck[-1])
		self.player_deck.colors = {}
		for pile in self.player_deck.deck:
			for card in pile:
				if card.color not in self.player_deck.colors.keys():
					self.player_deck.colors[card.color] = 0
				self.player_deck.colors[card.color] += 1
		# Prepare infection deck
		single_pile = [card for pile in self.infection_deck.deck for card in pile]
		single_pile.extend(self.infection_deck.discard)
		single_pile.sort(key = lambda x: str(x))
		self.prng.shuffle(single_pile)
		self.infection_deck.deck = [single_pile]
		self.infection_deck.discard = []
		# Set initial infections
		for i in range(9):
			city = self.cities[self.infection_deck.draw().name]
			city.infect(self,infection=(i//3)+1,color=city.color,outbreak_chain=[])
		# Post setup players
		for player in self.players:
			player.move_triggers(self)
		# Start game
		self.rstate=self.prng.getstate()
		self.commons['error_flag'] = False
		self.current_player = starting_player
		self.real_current_player = None
		self.current_turn = 1
		self.turn_phase = TurnPhase.NEW
		self.game_state = GameState.PLAYING
		self.commons['record'] = {}
		# Final step
		self.id = hash(self.get_id())
	### Utility function, do not call (public cause Player-class needs to call it when building a new RS)
	def calculate_distances(self):
		city_distances = {
				key: {target: (0 if target==key else (1 if target in self.cities[key].neighbors else len(self.cities))) for target in self.cities} for key in self.cities		
		}
		research_cities = [city for city in self.cities if self.cities[city].research_station]
		for rs in research_cities:
			for target in research_cities:
				if rs!=target:
					city_distances[rs][target] = 1
		for key in city_distances:
			unvisited = list(self.cities.keys())
			while unvisited:
				current_node = unvisited[0]
				current_distance = city_distances[key][current_node]
				for node in unvisited:
					if city_distances[key][node] < current_distance:
						current_node = node
						current_distance = city_distances[key][node]
				for neighbor in self.cities[current_node].neighbors:
					new_distance = current_distance + 1
					if new_distance < city_distances[key][neighbor]:
						city_distances[key][neighbor] = new_distance
				unvisited.remove(current_node)
		self.distances = city_distances
		self.total_distances = sum(sum(d.values()) for d in self.distances.values())
	### Status check functions
	def lost(self):
		return self.player_deck.remaining<0 or min(self.remaining_disease_cubes.values())<0 or self.outbreak_counter>=8
	def won(self):
		return all(self.cures.values())
	### Phase changing actions -> must be executed according to current state
	def start_turn(self):
		valid = self.turn_phase == TurnPhase.NEW
		if valid:
			self.log("Turn begin: "+self.players[self.current_player].playerrole.name)
			self.actions = 4
			self.turn_phase = TurnPhase.ACTIONS
			if self.record_actions:
				self.commons['record'][self.current_turn] = []
		else:
			print("Invalid turn start, current turn phase: "+self.turn_phase.name)
		return valid
		
	def do_action(self,action,kwargs):
		valid = self.turn_phase == TurnPhase.ACTIONS and action!=self.players[self.current_player].discard.__name__
		if valid:
			try:
				if self.record_actions:
					self.commons['record'][self.current_turn].append((copy.copy(self),self.current_player,action,kwargs))
				self.players = copy.copy(self.players)
				self.players[self.current_player] = copy.copy(self.players[self.current_player])
				if self.players[self.current_player].perform_action(self,action,kwargs):
					self.actions -= 1
					# Check if still in ACTIONS to see if DISCARD interruption occured
					if self.actions == 0 and self.turn_phase == TurnPhase.ACTIONS:
						self.turn_phase = TurnPhase.DRAW
				else:
					if self.record_actions:
						self.commons['record'][self.current_turn].pop()
					valid = False
					print("Invalid move or something")
					print(self.players[self.current_player])
					print("Tried to do:",action,kwargs)
					print("In game state:",self)
					self.commons['error_flag']=True
			except:
				print("Error, wrong function or something.")
				print("Action:",action)
				print("kwargs:",kwargs)
				traceback.print_exc()
				self.turn_phase = TurnPhase.INACTIVE
				self.commons['error_flag'] = True
			if self.won():
				self.turn_phase = TurnPhase.INACTIVE
				self.game_state = GameState.WON
				self.log("Players have WON the game")
		else:
			print("Invalid do action, current turn phase: "+self.turn_phase.name)
		return valid
	
	def draw_phase(self):
		valid = self.turn_phase == TurnPhase.DRAW
		if valid:
			self.players = copy.copy(self.players)
			self.players[self.current_player] = copy.copy(self.players[self.current_player])
			self.players[self.current_player].draw(self,2)
			if self.lost():
				self.turn_phase = TurnPhase.INACTIVE
				self.game_state = GameState.LOST
				self.log("Players have LOST the game")
			elif self.players[self.current_player].must_discard():
				self.turn_phase = TurnPhase.DISCARD
			else:
				self.turn_phase = TurnPhase.INFECT
		return valid
	
	def do_discard(self,discard):
		valid = self.turn_phase == TurnPhase.DISCARD
		if valid:
			if self.record_actions:
				self.commons['record'][self.current_turn].append((copy.copy(self),self.current_player,Player.discard.__name__,{'card':discard}))
			self.players = copy.copy(self.players)
			self.players[self.current_player] = copy.copy(self.players[self.current_player])
			if self.players[self.current_player].discard(self,discard):
				if not self.players[self.current_player].must_discard():
					if self.real_current_player == None:
						self.turn_phase = TurnPhase.INFECT
					else:
						self.current_player = self.real_current_player
						self.real_current_player = None
						self.turn_phase = TurnPhase.ACTIONS if self.actions > 0 else TurnPhase.DRAW
			else:
				if self.record_actions:
					self.commons['record'][self.current_turn].pop()
				print("Invalid card discard")
		else:
			print("Invalid do discard, current turn phase: "+self.turn_phase.name)
		return valid
	
	def end_turn(self):
		valid = self.turn_phase == TurnPhase.INFECT
		if valid:
			self.cities = copy.copy(self.cities)
			for i in range(self.infection_rate):
				self.infection_deck = copy.copy(self.infection_deck)
				city_name = self.infection_deck.draw().name
				self.cities[city_name] = copy.copy(self.cities[city_name])
				city = self.cities[city_name]
				city.infect(self,infection=1,color=city.color,outbreak_chain=[])
			self.current_player = (self.current_player+1)%len(self.players)
			if self.lost():
				self.turn_phase = TurnPhase.INACTIVE
				self.game_state = GameState.LOST
				self.log("Players have LOST the game")
			else:
				self.current_turn += 1
				self.turn_phase = TurnPhase.NEW
		else:
			print("Invalid end turn, current turn phase: "+self.turn_phase.name)
		return valid
	### Game execution functions, usually with game_loop is enough
	def game_advance(self):
		while self.turn_phase not in [TurnPhase.INACTIVE, TurnPhase.ACTIONS, TurnPhase.DISCARD]:
			if self.turn_phase == TurnPhase.NEW:
				self.start_turn()
			if self.turn_phase==TurnPhase.DRAW:
				self.draw_phase()
			if self.turn_phase == TurnPhase.INFECT:
				self.end_turn()
	
	def game_turn(self):
		if self.turn_phase == TurnPhase.NEW:
			self.start_turn()
		while self.turn_phase == TurnPhase.ACTIONS or self.turn_phase == TurnPhase.DISCARD:
			if self.turn_phase == TurnPhase.ACTIONS:
				action, kwargs = self.players[self.current_player].request_action(self)
				self.do_action(action,kwargs)
			else:
				discard = self.players[self.current_player].request_discard(self)
				self.do_discard(discard)
		if self.turn_phase==TurnPhase.DRAW:
			self.draw_phase()
		while self.turn_phase == TurnPhase.DISCARD:
			discard = self.players[self.current_player].request_discard(self)
			self.do_discard(discard)
		if self.turn_phase == TurnPhase.INFECT:
			self.end_turn()

	def game_loop(self):
		self.log("Starting game")
		while self.game_state == GameState.PLAYING and self.turn_phase!= TurnPhase.INACTIVE:
			self.game_turn()
		if self.game_state == GameState.WON:
			self.log("Players won the game")
		elif self.game_state == GameState.LOST:
			self.log("Players lost the game")
		else:
			self.log("This should not happen")
	
class Card:
	def __repr__(self):
		return self.name
	
	def __init__(self,name,cardtype,color=None):
		self.name = name
		self.cardtype = cardtype
		self.color = color
	
	def __eq__(self,other):
		return self.name == other
	
class City:
	def __repr__(self):
		return self.name+": Diseases: "+str([color+"="+str(self.disease_cubes[color]) for color in self.disease_cubes]) + " R.S: "+str(1 if self.research_station else 0)
	
	def __call__(self):
		return {
			'disease_cubes': self.disease_cubes,
			'research_station': self.research_station
		}
	
	def __init__(self,name,color,neighbors,colors):
		self.name = name
		self.color = color
		self.neighbors = neighbors
		self.disease_cubes = {c: 0 for c in colors}
		self.research_station = False
	
	def get_id(self):
		return (
				tuple(self.disease_cubes.values()),
				self.research_station
		)
	
	def infect(self,game,infection,color,outbreak_chain):
		if not game.eradicated[color] and self.name not in game.protected_cities and not (game.medic_position==self.name and game.cures[color]):
			net_infection = min(3-self.disease_cubes[color],infection)
			self.disease_cubes = copy.copy(self.disease_cubes)
			self.disease_cubes[color] += net_infection
			game.remaining_disease_cubes = copy.copy(game.remaining_disease_cubes)
			game.remaining_disease_cubes[color] -= net_infection
			game.log("Infect "+str(net_infection)+"-"+color+" at: "+self.name)
			# Outbreak
			if infection > net_infection:
				game.log("Outbreak at: "+self.name)
				outbreak_chain.append(self.name)
				game.outbreak_counter += 1
				for city_name in self.neighbors:
					if city_name not in outbreak_chain:
						game.cities[city_name] = copy.copy(game.cities[city_name])
						game.cities[city_name].infect(game,1,color,outbreak_chain)
		else:
			game.log("Infection prevented at: "+self.name)
			
	def disinfect(self,game,disinfection,color):
		self.disease_cubes = copy.copy(self.disease_cubes)
		self.disease_cubes[color] -= disinfection
		game.remaining_disease_cubes = copy.copy(game.remaining_disease_cubes)
		game.remaining_disease_cubes[color] += disinfection
		if game.cures[color] and game.remaining_disease_cubes[color]==game.commons['number_cubes']:
			game.eradicated = copy.copy(game.eradicated)
			game.eradicated[color] = True
			game.log("Eradicated "+color+" disease")
	
class Player:
	def __repr__(self):
		return self.playerrole.name+" Current location: "+str(self.position)+" - Cards: "+str(self.cards)
	
	def __call__(self):
		return {
			'location': self.position,
			'role': self.playerrole.name,
			'cards': [card.name for card in self.cards]
		}
	
	def __init__(self):
		self.pid = -1
		self.cards = []
		self.position = None
		self.playerrole = PlayerRole.NULL
		self.colors = {}
		
	def get_id(self):
		return (self.position,tuple(c.name for c in self.cards))
		
	def draw(self,game,amount):
		game.player_deck = copy.copy(game.player_deck)
		self.cards = copy.copy(self.cards)
		for c in range(amount):
			card = game.player_deck.draw()
			if card.cardtype == CardType.EPIDEMIC:
				# Increase infection counter
				game.infection_counter += 1
				if game.infection_counter == 3 or game.infection_counter == 5:
					game.infection_rate+=1
				# Infect x3 bottom card				
				game.infection_deck = copy.copy(game.infection_deck)
				city_name = game.infection_deck.draw_bottom().name
				game.log(self.playerrole.name+" drew: epidemic\nEpidemic at: "+city_name)
				game.cities = copy.copy(game.cities)
				game.cities[city_name] = copy.copy(game.cities[city_name])
				city = game.cities[city_name]
				city.infect(game,infection=3,color=city.color,outbreak_chain=[])
				# Shuffle infect discard pile
				game.infection_deck.intensify(game)
			elif card.cardtype != CardType.MISSING:
				game.log(self.playerrole.name+" drew: "+card.name)
				self.colors = copy.copy(self.colors)
				self.colors[card.color]+=1
				# Normal card
				self.cards.append(card)
		# Draws at end of turn, so resets Operations Expert special ability
		if self.playerrole==PlayerRole.OPERATIONS_EXPERT:
			self.special_move = True
		
	def move_triggers(self,game):
		if self.playerrole == PlayerRole.MEDIC:
			game.medic_position = self.position
			for color in game.cures:
				if game.cures[color] and game.cities[self.position].disease_cubes[color]>0:
					game.cities = copy.copy(game.cities)
					game.cities[self.position] = copy.copy(game.cities[self.position])
					game.cities[self.position].disinfect(game,game.cities[self.position].disease_cubes[color],color)
					game.log("MEDIC healed "+str(color)+" at: "+str(self.position))
		elif self.playerrole == PlayerRole.QUARANTINE_SPECIALIST:
			game.protected_cities = [self.position]
			game.protected_cities.extend(game.cities[self.position].neighbors)
	
	def must_discard(self):
		return len(self.cards)>7
		
	def no_action(self):
		return True
		
	# Stub function, must be implemented in child
	def request_action(self,game):
		return self.no_action.__name__,{}
		
	# Stub function, must be implemented in child
	def request_discard(self,game):
		return self.cards[0]
	
	def perform_action(self,game,action,kwargs):
		actions = {
			self.no_action.__name__: self.no_action,
			self.discard.__name__: self.discard,
			self.drive_ferry.__name__: self.drive_ferry,
			self.direct_flight.__name__: self.direct_flight,
			self.charter_flight.__name__: self.charter_flight,
			self.shuttle_flight.__name__: self.shuttle_flight,
			self.build_researchstation.__name__: self.build_researchstation ,
			self.treat_disease.__name__: self.treat_disease,
			self.give_knowledge.__name__: self.give_knowledge,
			self.receive_knowledge.__name__: self.receive_knowledge,
			self.discover_cure.__name__: self.discover_cure,
			self.rally_flight.__name__: self.rally_flight,
			self.special_charter_flight.__name__: self.special_charter_flight
		}
		return actions[action](game,**kwargs) if action in actions else False
	
	def available_actions(self,game):
		valid_cities = [city for city in game.cities if city!=self.position]
		actions = {}
		if game.turn_phase==TurnPhase.ACTIONS:
			actions[self.drive_ferry.__name__] = [ {'target':city} for city in game.cities[self.position].neighbors ]
			actions[self.direct_flight.__name__] = [ {'target':card.name} for card in self.cards if (card.cardtype==CardType.CITY and card.name!=self.position) ]
			actions[self.charter_flight.__name__] = [ {'target':city} for city in valid_cities] if self.position in self.cards else []
			actions[self.shuttle_flight.__name__] = [ {'target':city} for city in valid_cities if game.cities[city].research_station] if (game.cities[self.position].research_station and game.research_station_counter>1) else []
			actions[self.build_researchstation.__name__] = ([{'replace':"none"}] if game.research_station_counter < 6 else [{'replace':city} for city in game.cities if game.cities[city].research_station]) if ((self.position in self.cards or self.playerrole == PlayerRole.OPERATIONS_EXPERT) and not game.cities[self.position].research_station) else []
			actions[self.treat_disease.__name__] = [ {'color':color} for color in game.commons['colors'] if game.cities[self.position].disease_cubes[color]>0 ]
			actions[self.give_knowledge.__name__] = [{'receiver':player.pid, 'target':card.name} for player in game.players for card in self.cards  if (player!=self and self.position==player.position and card.cardtype==CardType.CITY and (self.position==card.name or self.playerrole==PlayerRole.RESEARCHER))]
			actions[self.receive_knowledge.__name__] = [{'giver':player.pid, 'target':card.name} for player in game.players for card in player.cards if (player!=self and self.position==player.position and card.cardtype==CardType.CITY and (self.position==card.name or player.playerrole==PlayerRole.RESEARCHER))]
			actions[self.discover_cure.__name__] = [{'color':color,'chosen_cards':[self.cards[i].name for i in chosen_cards]} for chosen_cards in list(itertools.combinations(np.arange(len(self.cards)),4 if self.playerrole==PlayerRole.SCIENTIST else 5)) for color in game.commons['colors'] if all([city in game.cities.keys() and game.cities[city].color==color for city in [self.cards[i].name for i in chosen_cards]])] if game.cities[self.position].research_station and len(self.cards)>=(4 if self.playerrole==PlayerRole.SCIENTIST else 5) else []
			actions[self.rally_flight.__name__] = [{'player':player.pid,'target_player':target.pid} for player in game.players for target in game.players if player.position!=target.position] if self.playerrole==PlayerRole.DISPATCHER else []
			actions[self.special_charter_flight.__name__] = [{'discard':card.name,'target':city} for card in self.cards for city in valid_cities if card.name in game.cities.keys()] if self.playerrole==PlayerRole.OPERATIONS_EXPERT and self.special_move and game.cities[self.position].research_station else []
		elif game.turn_phase==TurnPhase.DISCARD:
			actions[self.discard.__name__] = [{'discard':card.name} for card in self.cards]
		return actions

	# Card is a string with the card name
	def discard(self,game,card):
		valid = card in self.cards
		if valid:
			game.log(self.playerrole.name+" discarded: "+card)
			self.cards = copy.copy(self.cards)
			game.player_deck = copy.copy(game.player_deck)
			card = self.cards.pop(self.cards.index(card))
			self.colors = copy.copy(self.colors)
			self.colors[card.color]-=1
			game.player_deck.discard = copy.copy(game.player_deck.discard)
			game.player_deck.discard.append(card)
		return valid
	
	# Target is string object to new position
	def drive_ferry(self,game,target):
		valid = target in game.cities[self.position].neighbors
		if valid:
			game.log(self.playerrole.name+" drove to: "+target)
			self.position = target
			self.move_triggers(game)
		return valid
	
	# Target is string object to new position
	def direct_flight(self,game,target):
		valid = target in self.cards and self.position!=target and target in game.cities.keys()
		if valid:
			game.log(self.playerrole.name+" direct flew to: "+target)
			self.discard(game,target)
			self.position = target
			self.move_triggers(game)
		return valid
	
	# Target is string object to new position
	def charter_flight(self,game,target):
		valid = self.position in self.cards and self.position!=target and target in game.cities.keys()
		if valid:
			game.log(self.playerrole.name+" charter flew to: "+target)
			self.discard(game,self.position)
			self.position = target
			self.move_triggers(game)
		return valid
	
	# Target is string object to new position
	def shuttle_flight(self,game,target):
		valid = game.cities[self.position].research_station and self.position!=target and target in game.cities.keys() and game.cities[target].research_station
		if valid:
			game.log(self.playerrole.name+" shuttle flew to: "+target)
			self.position = target
			self.move_triggers(game)
		return valid
	
	# Replace is None or string of city name in which research_station will be removed
	def build_researchstation(self,game,replace=None):
		if replace=="none":
			replace=None
		valid = (self.position in self.cards or self.playerrole == PlayerRole.OPERATIONS_EXPERT) and not game.cities[self.position].research_station and (game.research_station_counter<6 or (replace in game.cities.keys() and game.cities[replace].research_station))
		if valid:
			game.log(self.playerrole.name+" built research station")
			game.cities = copy.copy(game.cities)
			game.cities_rs = copy.copy(game.cities_rs)
			if game.research_station_counter == 6:
				game.cities[replace] = copy.copy(game.cities[replace])
				game.cities[replace].research_station = False
				game.cities_rs.remove(replace)
				game.log(self.playerrole.name+" removed research station at: "+replace)
			else:
				game.research_station_counter += 1
			if self.playerrole != PlayerRole.OPERATIONS_EXPERT:
				self.discard(game,self.position)
			game.cities[self.position] = copy.copy(game.cities[self.position])
			game.cities[self.position].research_station = True
			game.cities_rs.append(self.position)
			game.calculate_distances()
		return valid
	
	# Color is string object of the color name
	def treat_disease(self,game,color):
		valid = game.cities[self.position].disease_cubes[color] > 0
		if valid:
			treated = game.cities[self.position].disease_cubes[color] if (self.playerrole == PlayerRole.MEDIC or game.cures[color]) else 1
			game.cities = copy.copy(game.cities)
			game.cities[self.position] = copy.copy(game.cities[self.position])
			game.cities[self.position].disinfect(game,treated,color)
			game.log(self.playerrole.name+" "+str(treated)+"-treated: "+color)
		return valid
	
	def transfer_card(self,game,target,receiver,giver):
		giver.cards = copy.copy(giver.cards)
		giver.colors = copy.copy(giver.colors)
		receiver.cards = copy.copy(receiver.cards)
		receiver.colors = copy.copy(receiver.colors)
		card = giver.cards.pop(giver.cards.index(target))
		receiver.cards.append(card)
		giver.colors[card.color]-=1
		receiver.colors[card.color]+=1
		if receiver.must_discard():
			game.log(receiver.playerrole.name+" must discard")
			game.real_current_player = game.current_player
			game.current_player = receiver.pid
			game.turn_phase = TurnPhase.DISCARD
	
	# Receiver is pid number, target is string object
	def give_knowledge(self,game,receiver,target):
		game.players[receiver  % len(game.players)] = copy.copy(game.players[receiver  % len(game.players)])
		receiver_player = game.players[receiver  % len(game.players)]
		valid = receiver_player!=self and self.position==receiver_player.position and target in self.cards and (self.position==target or self.playerrole==PlayerRole.RESEARCHER)
		if valid:
			game.log(self.playerrole.name+" gave "+target+" to: "+receiver_player.playerrole.name)
			self.transfer_card(game,target,receiver_player,self)
		return valid
	
	# Giver is pid number, target is string object
	def receive_knowledge(self,game,giver,target):
		game.players[giver % len(game.players)] = copy.copy(game.players[giver % len(game.players)])
		giver = game.players[giver % len(game.players)]
		valid = giver!=self and self.position==giver.position and target in giver.cards and (self.position==target or giver.playerrole==PlayerRole.RESEARCHER)
		if valid:
			game.log(self.playerrole.name+" received "+target+" from: "+giver.playerrole.name)
			self.transfer_card(game,target,self,giver)
		return valid
	
	# Color is a string object, chosen_cards is an array containing string objects
	def discover_cure(self,game,color,chosen_cards):
		valid = game.cities[self.position].research_station and len(chosen_cards)==(4 if self.playerrole==PlayerRole.SCIENTIST else 5) and all([(card in self.cards and self.cards[self.cards.index(card)].cardtype==CardType.CITY and game.cities[card].color==color) for card in chosen_cards])
		if valid:
			game.log(self.playerrole.name+" discovered cure for: "+color)
			for card in chosen_cards:
				self.discard(game,card)
			game.cures = copy.copy(game.cures)
			game.cures[color] = True
			if game.remaining_disease_cubes[color]==game.commons['number_cubes']:
				game.eradicated = copy.copy(game.eradicated)
				game.eradicated[color] = True
				game.log("Eradicated "+color+" disease")
			for player in game.players:
				if player.playerrole == PlayerRole.MEDIC:
					player.move_triggers(game)
		return valid
	
	# Player is pid number, target_player is pid number
	def rally_flight(self,game,player,target_player):
		game.players[player % len(game.players)] = copy.copy(game.players[player % len(game.players)])
		player = game.players[player % len(game.players)]
		target_player = game.players[target_player % len(game.players)]
		valid = self.playerrole==PlayerRole.DISPATCHER and player.position!=target_player.position
		if valid:
			game.log("DISPATCHER rallied "+player.playerrole.name+" to: "+target_player.playerrole.name)
			player.position = target_player.position
			player.move_triggers(game)
		return valid
	
	# Discard is a string of card name, target is a string to new location
	def special_charter_flight(self,game,discard,target):
		valid = self.playerrole==PlayerRole.OPERATIONS_EXPERT and self.special_move and game.cities[self.position].research_station and discard in self.cards and discard in game.cities.keys() and target!=self.position
		if valid:
			game.log(self.playerrole.name+" special charter flew to: "+target+" discarding: "+discard)
			self.special_move = False
			self.discard(game,discard)
			self.position = target
		return valid
	
	# TODO: Implement different event actions
	def use_event(self,event):
		pass
	
class PlayerDeck:
	def __repr__(self):
		return "Expecting epidemic: "+str(1 if self.expecting_epidemic else 0)+", Next epidemic in: "+str(self.epidemic_countdown)+", Remaining cards: "+str(self.remaining)
	
	def __call__(self):
		remaining_cards = [card.name for pile in self.deck for card in pile]
		remaining_cards.sort()
		return {
			'cards_left': self.remaining,
			'deck': remaining_cards,
			'discard': [card.name for card in self.discard],
			'epidemic_countdown': self.epidemic_countdown,
			'epidemic_expectation': self.expecting_epidemic
		}
	
	def __init__(self,cards):
		self.deck = [cards.copy()]
		self.discard = []
		self.remaining = 0
		self.expecting_epidemic = False
		self.epidemic_countdown = 0
		self.colors = {}
		
	def draw(self):
		if len(self.deck)>0:
			self.deck = copy.copy(self.deck)
			self.deck[-1] = copy.copy(self.deck[-1])
			self.colors = copy.copy(self.colors)
			card = self.deck[-1].pop()
			self.colors[card.color] -= 1
			self.remaining -= 1
			self.epidemic_countdown -= 1
			self.expecting_epidemic = self.expecting_epidemic and card.cardtype!=CardType.EPIDEMIC
			if len(self.deck[-1])==0:
				self.deck.pop()
				self.expecting_epidemic = True
				self.epidemic_countdown = len(self.deck[-1]) if len(self.deck)>0 else 0
		else:
			self.remaining -= 1
			card = Card(name="",cardtype=CardType.MISSING)
		return card
	
	@property
	def chances_epidemic(self):
		if self.epidemic_countdown>=2:
			return self.expecting_epidemic*2/len(self.deck[-1])
		else:
			return ((self.remaining>=2)/len(self.deck[-2])) + self.expecting_epidemic
	
	def get_possible_deck(self,prng):
		pile_info = [[len(pile),any([card.cardtype==CardType.EPIDEMIC for card in pile])] for pile in self.deck]		
		cards = [card for pile in self.deck for card in pile if card.cardtype != CardType.EPIDEMIC]
		deck = []
		prng.shuffle(cards)
		for p in pile_info:
			pile = [Card(name="Epidemic",cardtype=CardType.EPIDEMIC,color="epidemic")] if p[1] else []
			for c in range(len(pile),p[0]):
				pile.append(cards.pop())
			prng.shuffle(pile)
			deck.append(pile)
		return deck
	
class InfectionDeck:
	def __repr__(self):
		return "Possible next cards: "+str(self.known_cards)
	
	def __call__(self):
		return {
			'known_piles': self.known_cards,
			'discard': [card.name for card in self.discard]
		}
	
	def __init__(self,cities):
		self.deck = [cities.copy()]
		self.discard = []
		
	def draw(self):
		self.deck = copy.copy(self.deck)
		self.deck[-1] = copy.copy(self.deck[-1])
		card = self.deck[-1].pop()
		if len(self.deck[-1])==0:
			self.deck.pop()
		self.discard = copy.copy(self.discard)
		self.discard.append(card)
		return card
		
	def draw_bottom(self):
		self.deck = copy.copy(self.deck)
		self.deck[0] = copy.copy(self.deck[0])
		city = self.deck[0].pop(0)
		if len(self.deck[0])==0:
			self.deck.pop(0)
		self.discard = copy.copy(self.discard)
		self.discard.append(city)
		return city
	
	def intensify(self,game):
		self.deck = copy.copy(self.deck)
		self.discard = copy.copy(self.discard)
		game.prng.setstate(game.rstate)
		game.prng.shuffle(self.discard)
		game.rstate=game.prng.getstate()
		self.deck.append(self.discard)
		self.discard = []
		
	@property
	def known_cards(self):
		known_cards = [[card.name for card in pile] for pile in self.deck]
		for pile in known_cards:
			pile.sort()
		return known_cards
		
	def get_possible_deck(self,prng):
		deck = []
		for pile in self.deck:
			new_pile = copy.copy(pile)
			prng.shuffle(new_pile)
			deck.append(new_pile)
		return deck

if __name__ == '__main__':
	from Players import RandomPlayer,HeuristicPlayer,PlanningPlayer
	game = Game([PlanningPlayer(),PlanningPlayer()],external_log = sys.stdout )
	game.setup(players_roles=[PlayerRole.SCIENTIST,PlayerRole.RESEARCHER],seed=777)
	for i in range(23):
		game.game_turn()
		
"""
Expected output of test:
	Roles=SCIENTIST,RESEARCHER
	Seed=21
	Setting game up
	SCIENTIST drew: delhi
	SCIENTIST drew: manila
	SCIENTIST drew: taipei
	SCIENTIST drew: tokyo
	RESEARCHER drew: seoul
	RESEARCHER drew: khartoum
	RESEARCHER drew: montreal
	RESEARCHER drew: hong_kong
	Infect 1-blue at: paris
	Infect 1-yellow at: santiago
	Infect 1-blue at: new_york
	Infect 2-black at: istanbul
	Infect 2-black at: riyadh
	Infect 2-red at: tokyo
	Infect 3-black at: kolkata
	Infect 3-blue at: washington
	Infect 3-yellow at: sao_paulo
	Turn begin: RESEARCHER
	RESEARCHER gave seoul to: SCIENTIST
	RESEARCHER drove to: washington
	RESEARCHER direct flew to: hong_kong
	RESEARCHER discarded: hong_kong
	RESEARCHER direct flew to: khartoum
	RESEARCHER discarded: khartoum
	RESEARCHER drew: cairo
	RESEARCHER drew: osaka
	Infect 1-black at: cairo
	Infect 1-blue at: essen
	Turn begin: SCIENTIST
	SCIENTIST direct flew to: tokyo
	SCIENTIST discarded: tokyo
	SCIENTIST drove to: osaka
	SCIENTIST direct flew to: manila
	SCIENTIST discarded: manila
	SCIENTIST drove to: san_francisco
	SCIENTIST drew: epidemic
	Epidemic at: karachi
	Infect 3-black at: karachi
	SCIENTIST drew: lima
	Infect 1-blue at: paris
	Infect 1-black at: riyadh
	Turn begin: RESEARCHER
	RESEARCHER direct flew to: osaka
	RESEARCHER discarded: osaka
	RESEARCHER drove to: taipei
	RESEARCHER drove to: osaka
	RESEARCHER direct flew to: montreal
	RESEARCHER discarded: montreal
	RESEARCHER drew: baghdad
	RESEARCHER drew: kolkata
	Infect 0-black at: karachi
	Outbreak at: karachi
	Infect 1-black at: baghdad
	Infect 0-black at: riyadh
	Outbreak at: riyadh
	Infect 1-black at: cairo
	Infect 1-black at: baghdad
	Infect 1-black at: tehran
	Infect 1-black at: delhi
	Infect 1-black at: mumbai
	Infect 1-blue at: essen
"""
	