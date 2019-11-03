# -*- coding: utf-8 -*-
"""
@author: Blopa
"""

import copy
import itertools
import numpy as np
import random
import sys
import traceback
from enum import IntEnum, auto
from city_cards import city_cards

debug_console = False

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


class Game():
	commons = {}
	
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
	
	def __init__(self,players,epidemic_cards=4,cities=city_cards,starting_city="atlanta",number_cubes=24,log_game=True):
		assert(starting_city in cities)
		# Save game parameters
		self.commons['epidemic_cards'] = epidemic_cards
		self.commons['starting_city'] = starting_city
		self.commons['number_cubes'] = number_cubes
		self.commons['colors'] = []
		self.commons['logger'] = sys.stdout if debug_console else None
		self.commons['log_game'] = log_game
		self.commons['game_log'] = ""
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
		# Turn controls
		self.current_player = -1
		self.current_turn = -1
		self.turn_phase = TurnPhase.INACTIVE
		self.game_state = GameState.NOT_PLAYING
	
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
	
	def log(self,new_log):
		if self.commons['log_game']:
			self.commons['game_log'] += new_log+"\n"
		if self.commons['logger'] is not None:
			self.commons['logger'].write(new_log+"\n")
	
	def setup(self,players_roles=None):
		self.log("Setting game up")
		if players_roles is None or len(players_roles)!=len(self.players):
			roles = list(PlayerRole)
			roles.remove(PlayerRole.NULL)
			# TODO: DISPATCHER and CONTINGENCY_PLANNER NOT FULLY IMPLEMENTED
			roles.remove(PlayerRole.CONTINGENCY_PLANNER)
			roles.remove(PlayerRole.DISPATCHER)
			# REMOVED OPERATIONS_EXPERT BECAUSE OF SEARCH SPACE EXPLOSION
			roles.remove(PlayerRole.OPERATIONS_EXPERT)
			players_roles = random.sample(roles,len(self.players))
		# Player setup
		for p,player in enumerate(self.players):
			player.pid = p
			player.position = self.commons['starting_city']
			player.playerrole = players_roles[p]
			if player.playerrole == PlayerRole.OPERATIONS_EXPERT:
				player.special_move = False
			self.player_deck.discard.extend(player.cards)
			player.cards = []
		# City setup
		for c in self.cities:
			city = self.cities[c]
			# Restarts disease cubes and research station flag
			for color in city.disease_cubes:
				city.disease_cubes[color] = 0
			city.research_station = False
		self.cities[self.commons['starting_city']].research_station = True
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
		self.player_deck.discard = []
		random.shuffle(self.player_deck.deck)
		# Deal players' hands
		for player in self.players:
			for c in range(6-len(self.players)):
				card = self.player_deck.deck.pop()
				self.log(player.playerrole.name+" drew: "+card.name)
				player.cards.append(card)
		self.player_deck.missing = False
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
			random.shuffle(pile)
			self.player_deck.deck.append(pile)
		self.player_deck.count_colors()
		# Reset infection deck
		single_pile = [card for pile in self.infection_deck.deck for card in pile]
		single_pile.extend(self.infection_deck.discard)
		random.shuffle(single_pile)
		self.infection_deck.deck = [single_pile]
		self.infection_deck.discard = []
		# Set initial infections
		for i in range(9):
			city = self.cities[self.infection_deck.draw().name]
			city.infect(self,infection=(i//3)+1,color=city.color)
		# Post setup players
		for player in self.players:
			player.move_triggers(self)
		# Start game
		self.commons['error_flag'] = False
		self.commons['game_log'] = ""
		self.current_player = starting_player
		self.real_current_player = None
		self.current_turn = 1
		self.turn_phase = TurnPhase.NEW
		self.game_state = GameState.PLAYING
		
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
		
	def eradication_check(self):
		for color in self.commons['colors']:
			if self.cures[color] and not self.eradicated[color] and self.remaining_disease_cubes[color]==self.commons['number_cubes']:
				self.eradicated = copy.copy(self.eradicated)
				self.eradicated[color] = True
				self.log("Eradicated "+color+" disease")
	
	def lost(self):
		return self.player_deck.out_of_cards() or min(self.remaining_disease_cubes.values())<0 or self.outbreak_counter>=8
	
	def won(self):
		return all(self.cures.values())
		
	def start_turn(self):
		valid = self.turn_phase == TurnPhase.NEW
		if valid:
			self.actions = 4
			self.turn_phase = TurnPhase.ACTIONS
		else:
			print("Invalid turn start, current turn phase: "+self.turn_phase.name)
		return valid
		
	def do_action(self,action,kwargs):
		valid = self.turn_phase == TurnPhase.ACTIONS and action!=self.players[self.current_player].discard.__name__
		if valid:
			try:
				self.players = copy.copy(self.players)
				self.players[self.current_player] = copy.copy(self.players[self.current_player])
				if self.players[self.current_player].perform_action(self,action,kwargs):
					self.actions -= 1
					# Check if still in ACTIONS to see if DISCARD interruption occured
					if self.actions == 0 and self.turn_phase == TurnPhase.ACTIONS:
						self.turn_phase = TurnPhase.DRAW
				else:
					valid = False
					print("Invalid move or something")
					print(self.players[self.current_player])
					print("Tried to do:",action,kwargs)	
			except:
				print("Error, wrong function or something.")
				print(action)
				print(kwargs)
				traceback.print_exc()
				self.turn_phase = TurnPhase.INACTIVE
				self.commons['error_flag'] = True
			# TODO: Can only check if action == Cure
			self.eradication_check()
			if self.won():
				self.turn_phase = TurnPhase.INACTIVE
				self.game_state = GameState.WON
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
			elif self.players[self.current_player].must_discard():
				self.turn_phase = TurnPhase.DISCARD
			else:
				self.turn_phase = TurnPhase.INFECT
		return valid
	
	def do_discard(self,discard):
		valid = self.turn_phase == TurnPhase.DISCARD
		if valid:
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
				print("Invalid card discard")
		else:
			print("Invalid do discard, current turn phase: "+self.turn_phase.name)
		return valid
	
	def end_turn(self):
		valid = self.turn_phase == TurnPhase.INFECT
		if valid:
			for i in range(self.infection_rate):
				self.infection_deck = copy.copy(self.infection_deck)
				city_name = self.infection_deck.draw().name
				self.cities[city_name] = copy.copy(self.cities[city_name])
				city = self.cities[city_name]
				city.infect(self,infection=1,color=city.color)
			self.current_player = (self.current_player+1)%len(self.players)
			if self.lost():
				self.turn_phase = TurnPhase.INACTIVE
				self.game_state = GameState.LOST
			else:
				self.current_turn += 1
				self.turn_phase = TurnPhase.NEW
		else:
			print("Invalid end turn, current turn phase: "+self.turn_phase.name)
		return valid
	
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
	
class Card(object):
	def __repr__(self):
		return self.name
	
	def __init__(self,name,cardtype,color=None):
		self.name = name
		self.cardtype = cardtype
		self.color = color
	
	def __eq__(self,other):
		return self.name == other
	
class City():
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
	
	def infect(self,game,infection,color,outbreak_chain=[]):
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
		
	
class Player():
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
				game.cities[city_name] = copy.copy(game.cities[city_name])
				city = game.cities[city_name]
				city.infect(game,infection=3,color=city.color)
				# Shuffle infect discard pile
				game.infection_deck.intensify()
			elif card.cardtype != CardType.MISSING:
				game.log(self.playerrole.name+" drew: "+card.name)
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
					game.cities[self.position] = copy.copy(game.cities[self.position])
					game.cities[self.position].disinfect(game,game.cities[self.position].disease_cubes[color],color)
					game.log("MEDIC healed "+str(color)+" at "+str(self.position))
		elif self.playerrole == PlayerRole.QUARANTINE_SPECIALIST:
			game.protected_cities = [self.position]
			game.protected_cities.extend(game.cities[self.position].neighbors)
	
	def must_discard(self):
		if self.playerrole == PlayerRole.CONTINGENCY_PLANNER:
			# TODO: Check if contingency planner has kept additional card
			return len(self.cards)>7
		else:
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
			game.player_deck.discard = copy.copy(game.player_deck.discard)
			game.player_deck.discard.append(self.cards.pop(self.cards.index(card)))
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
			if game.research_station_counter == 6:
				game.cities[replace] = copy.copy(game.cities[replace])
				game.cities[replace].research_station = False
				game.log(self.playerrole.name+" removed research station at: "+replace)
			else:
				game.research_station_counter += 1
			if self.playerrole != PlayerRole.OPERATIONS_EXPERT:
				self.discard(game,self.position)
			game.cities[self.position] = copy.copy(game.cities[self.position])
			game.cities[self.position].research_station = True
			game.calculate_distances()
		return valid
	
	# Color is string object of the color name
	def treat_disease(self,game,color):
		valid = game.cities[self.position].disease_cubes[color] > 0
		if valid:
			game.log(self.playerrole.name+" treated: "+color)
			game.cities[self.position] = copy.copy(game.cities[self.position])
			game.cities[self.position].disinfect(game,game.cities[self.position].disease_cubes[color] if (self.playerrole == PlayerRole.MEDIC or game.cures[color]) else 1 ,color)
		return valid
	
	# Receiver is pid number, target is string object
	def give_knowledge(self,game,receiver,target):
		game.players[receiver  % len(game.players)] = copy.copy(game.players[receiver  % len(game.players)])
		receiver_player = game.players[receiver  % len(game.players)]
		valid = receiver_player!=self and self.position==receiver_player.position and target in self.cards and (self.position==target or self.playerrole==PlayerRole.RESEARCHER)
		if valid:
			game.log(self.playerrole.name+" gave "+target+" to: "+receiver_player.playerrole.name)
			receiver_player.cards = copy.copy(receiver_player.cards)
			self.cards = copy.copy(self.cards)
			receiver_player.cards.append(self.cards.pop(self.cards.index(target)))
			if receiver_player.must_discard():
				game.real_current_player = game.current_player
				game.current_player = receiver
				game.turn_phase = TurnPhase.DISCARD
		return valid
	
	# Giver is pid number, target is string object
	def receive_knowledge(self,game,giver,target):
		game.players[giver % len(game.players)] = copy.copy(game.players[giver % len(game.players)])
		giver = game.players[giver % len(game.players)]
		valid = giver!=self and self.position==giver.position and target in giver.cards and (self.position==target or giver.playerrole==PlayerRole.RESEARCHER)
		if valid:
			game.log(self.playerrole.name+" received "+target+" from: "+giver.playerrole.name)
			giver.cards = copy.copy(giver.cards)
			self.cards = copy.copy(self.cards)
			self.cards.append(giver.cards.pop(giver.cards.index(target)))
			if self.must_discard():
				game.real_current_player = game.current_player
				game.turn_phase = TurnPhase.DISCARD
		return valid
	
	# Color is a string object, chosen_cards is an array containing string objects
	def discover_cure(self,game,color,chosen_cards):
		valid = game.cities[self.position].research_station and len(chosen_cards)==(4 if self.playerrole==PlayerRole.SCIENTIST else 5) and all([(card in self.cards and self.cards[self.cards.index(card)].cardtype==CardType.CITY and game.cities[card].color==color) for card in chosen_cards])
		if valid:
			game.log(self.playerrole.name+" found cure for: "+color)
			for card in chosen_cards:
				self.discard(game,card)
			game.cures = copy.copy(game.cures)
			game.cures[color] = True
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
	
class PlayerDeck():
	def __repr__(self):
		return "Expecting epidemic: "+str(1 if self.expecting_epidemic() else 0)+", Next epidemic in: "+str(self.epidemic_countdown())+", Remaining cards: "+str(self.cards_left())
	
	def __call__(self):
		remaining_cards = [card.name for pile in self.deck for card in pile]
		remaining_cards.sort()
		return {
			'cards_left': self.cards_left(),
			'deck': remaining_cards,
			'discard': [card.name for card in self.discard],
			'epidemic_countdown': self.epidemic_countdown(),
			'epidemic_expectation': self.expecting_epidemic()
		}
	
	def __init__(self,cards):
		self.deck = [cards.copy()]
		self.discard = []
		self.missing = False
		self.colors = {}
		
	def cards_left(self):
		return sum([len(pile) for pile in self.deck])
		
	def draw(self):
		if len(self.deck)>0:
			self.deck = copy.copy(self.deck)
			self.deck[-1] = copy.copy(self.deck[-1])
			self.colors = copy.copy(self.colors)
			card = self.deck[-1].pop()
			self.colors[card.color] -= 1
			if len(self.deck[-1])==0:
				self.deck.pop()
		else:
			card = Card(name="",cardtype=CardType.MISSING)
			self.missing = True
		return card
	
	def expecting_epidemic(self):
		return any([card.cardtype==CardType.EPIDEMIC for card in self.deck[-1]]) if len(self.deck)>1 else False
	
	def epidemic_countdown(self):
		return len(self.deck[-1]) if len(self.deck)>1 else 0
	
	def out_of_cards(self):
		return self.missing
	
	def count_colors(self):
		self.colors = {}
		for pile in self.deck:
			for card in pile:
				if card.color not in self.colors.keys():
					self.colors[card.color] = 0
				self.colors[card.color] += 1
	
class InfectionDeck():
	def __repr__(self):
		known_cards = [[card.name for card in pile] for pile in self.deck]
		for pile in known_cards:
			pile.sort()
		return "Possible next cards: "+str(known_cards)
	
	def __call__(self):
		known_cards = [[card.name for card in pile] for pile in self.deck]
		for pile in known_cards:
			pile.sort()
		return {
			'known_piles': known_cards,
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
	
	def intensify(self):
		self.deck = copy.copy(self.deck)
		self.discard = copy.copy(self.discard)
		random.shuffle(self.discard)
		self.deck.append(self.discard)
		self.discard = []

if __name__ == '__main__':
	from Players import RandomPlayer
	debug_console = True
	game = Game([RandomPlayer(),RandomPlayer()])
	game.setup()
	game.game_loop()