# -*- coding: utf-8 -*-
"""
@author: Blopa
"""

import itertools
import numpy as np
import random
import sys
from enum import IntEnum, auto
from city_cards import city_cards

debug_console = False

class Game(object):
	def __repr__(self):
		s = "Turn: "+str(self.turn_controller.current_turn)+", Current player: "+str(self.players[self.turn_controller.current_player].playerrole.name)+", Out.Counter: "+str(self.outbreak_counter)+", Inf.Counter: "+str(self.infection_counter)+", Inf.Rate: "+str(self.infection_rate)+"\n"
		s+= "Cures found: "+str([color+"="+str((2 if self.eradicated[color] else 1) if self.cures[color] else 0) for color in self.colors])+"\n"
		for p,player in enumerate(self.players):
			s += "Player "+str(p)+": "+str(player)+"\n"
		s+="Cities:\n"
		for city in self.cities:
			if self.cities[city].research_station or any([self.cities[city].disease_cubes[color]>0 for color in self.colors]):
				s += str(self.cities[city])+"\n"
		s+="Player deck: "+str(self.player_deck)+", Remaining by type: "+str(self.player_deck.remaining_cards(cities=self.cities,colors=self.colors))+", Total: "+str(len(self.player_deck.deck))+"\n"
		s+="Infection deck: "+str(self.infection_deck)
		return s
	
	def __init__(self,players,epidemic_cards=4,cities=city_cards,starting_city="atlanta",number_cubes=24):
		# Save game parameters
		self.epidemic_cards = epidemic_cards
		self.starting_city = starting_city
		self.number_cubes = number_cubes
		self.playing = False
		# Verify starting city
		assert(starting_city in cities)
		# Create players
		self.num_players = len(players)
		self.players = players
		for p,player in enumerate(self.players):
			player.assign(self,p)
		# Gather city colors and disease cubes
		self.colors = []
		for city in city_cards:
			if city_cards[city]['color'] not in self.colors:
				self.colors.append(city_cards[city]['color'])
		# Create cities
		self.cities = {city: City(game=self,name=city,color=city_cards[city]['color'],neighbors=city_cards[city]['connects'],colors=self.colors) for city in city_cards}
		# Create variables
		# TODO: event deck
		cities_deck = [Card(name=city,cardtype=CardType.CITY) for city in self.cities]
		event_deck = []
		self.player_deck = PlayerDeck(cities=cities_deck,events=event_deck)
		self.infection_deck = InfectionDeck(cities=cities_deck)
		self.turn_controller = PlayerTurn(game=self)
		# Start log system
		self.logger = sys.stdout if debug_console else None
		self.game_log = ""

	def __call__(self):
		game = {
			'game_state': self.turn_controller.game_state.name,
			'game_turn': self.turn_controller.current_turn,
			'turn_phase': self.turn_controller.turn_phase.name,
			'current_player': self.turn_controller.current_player,
			'infections': self.infection_counter,
			'infection_rate': self.infection_rate,
			'outbreaks': self.outbreak_counter,
			'cures': self.cures,
			'eradicated': self.eradicated,
			'disease_cubes': self.remaining_disease_cubes,
			'players': {"p"+str(p): self.players[p]() for p in range(self.num_players)},
			'cities': {city: self.cities[city]() for city in self.cities},
			'quarantine_cities': self.protected_cities,
			'infection_deck': self.infection_deck(),
			'player_deck': self.player_deck(),
			'actions': self.turn_controller.player.available_actions(),
			'remaining_actions': self.turn_controller.actions,
			'game_log': self.game_log
		}
		self.game_log = ""
		return game

	# TODO: Consider adding seeded decks to remove that randomness/noise
	def setup(self,players_roles=None):
		self.log("Setting game up")
		# Set players and players roles
		if players_roles is None or len(players_roles)!=len(self.players):
			roles = list(PlayerRole)
			roles.remove(PlayerRole.NULL)
			# TODO: DISPATCHER and CONTINGENCY_PLANNER NOT FULLY IMPLEMENTED
			roles.remove(PlayerRole.CONTINGENCY_PLANNER)
			roles.remove(PlayerRole.DISPATCHER)
			players_roles = random.sample(roles,len(self.players))
		for p, player in enumerate(self.players):
			player.setup(starting_city=self.starting_city, role=players_roles[p])
		# Set cities
		for c in self.cities:
			self.cities[c].setup()
		# Set counters
		self.remaining_disease_cubes = {color: self.number_cubes for color in self.colors}
		self.cures = {color: False for color in self.colors}
		self.eradicated = {color: False for color in self.colors}
		self.outbreak_chain = []
		self.outbreak_counter = 0
		self.infection_counter = 0
		self.infection_rate = 2
		self.research_station_counter = 1
		self.cities[self.starting_city].research_station = True
		self.protected_cities = []
		self.medic_position = None
		# Prepare player deck
		self.player_deck.presetup()
		# Deal players' hands
		for player in self.players:
			player.draw(6-self.num_players)
		# Define starting player
		maximum_population = 0
		starting_player = 0
		for p, player in enumerate(self.players):
			current_population = max([city_cards[card.name]['pop'] if card.cardtype==CardType.CITY else 0 for card in player.cards])
			if current_population >= maximum_population:
				starting_player = p
				maximum_population = current_population
		# Setup player deck
		self.player_deck.setup(epidemic_cards=self.epidemic_cards)
		# Reset infection deck
		self.infection_deck.setup()
		# Set initial infections
		for i in range(9):
			city = self.cities[self.infection_deck.draw().name]
			city.infect(infection=(i//3)+1,color=city.color)
		# Post setup players
		for player in self.players:
			player.postsetup()
		# Start game
		self.error_ocurred = False
		self.turn_controller.setup(starting_player)
	
	def eradication_check(self):
		for color in self.colors:
			if self.cures[color] and not self.eradicated[color] and self.remaining_disease_cubes[color]==self.number_cubes:
				self.eradicated[color] = True
				self.log("Eradicated "+color+" disease")
	
	def lost(self):
		return self.player_deck.out_of_cards or min(self.remaining_disease_cubes.values())<0 or self.outbreak_counter>=8
	
	def won(self):
		return all(self.cures.values())

	def game_turn(self):
		self.turn_controller.start_turn()
		while self.turn_controller.turn_phase == TurnPhase.ACTIONS:
			action, kwargs = self.turn_controller.player.request_action()
			self.turn_controller.do_action(action,kwargs)
		if self.turn_controller.turn_phase==TurnPhase.DRAW:
			self.turn_controller.draw_phase()
		while self.turn_controller.turn_phase == TurnPhase.DISCARD:
			discard = self.turn_controller.player.request_discard()
			self.turn_controller.do_discard(discard)
		self.turn_controller.end_turn()

	def game_loop(self):
		self.log("Starting game")
		while self.turn_controller.game_state == GameState.PLAYING:
			self.game_turn()
		if self.turn_controller.game_state == GameState.WON:
			self.log("Players won the game")
		elif self.turn_controller.game_state == GameState.LOST:
			self.log("Players lost the game")
				
	def log(self,new_log):
		self.game_log += new_log+"\n"
		if self.logger is not None:
			self.logger.write(new_log+"\n")
			
class CardType(IntEnum):
	MISSING = auto()
	CITY = auto()
	EVENT = auto()
	EPIDEMIC = auto()

class Card(object):
	def __repr__(self):
		return self.name
	
	def __init__(self,name,cardtype):
		self.name = name
		self.cardtype = cardtype
	
	def __eq__(self,other):
		return self.name == other
	
class City(object):
	def __repr__(self):
		return self.name+": Diseases: "+str([color+"="+str(self.disease_cubes[color]) for color in self.disease_cubes]) + " R.S: "+str(1 if self.research_station else 0)
		
	def __init__(self,game,name,color,neighbors,colors):
		# Gather city data
		self.game = game
		self.name = name
		self.color = color
		self.neighbors = neighbors
		self.disease_cubes = {c: 0 for c in colors}
		self.research_station = False
	
	def __call__(self):
		return {
			'disease_cubes': self.disease_cubes,
			'research_station': self.research_station
		}
	
	def setup(self):
		# Restarts disease cubes and research station flag
		for color in self.disease_cubes:
			self.disease_cubes[color] = 0
		self.research_station = False
		
	def infect(self,infection,color):
		if not self.game.eradicated[color] and self.name not in self.game.protected_cities and not (self.game.medic_position==self.name and self.game.cures[color]):
			net_infection = min(3-self.disease_cubes[color],infection)
			self.disease_cubes[color] += net_infection
			self.game.remaining_disease_cubes[color] -= net_infection
			self.game.log("Infect "+str(net_infection)+"-"+color+" at: "+self.name)
			# Outbreak
			if infection > net_infection:
				self.game.log("Outbreak at: "+self.name)
				self.game.outbreak_chain.append(self.name)
				self.game.outbreak_counter += 1
				for city_name in self.neighbors:
					if city_name not in self.game.outbreak_chain:
						self.game.cities[city_name].infect(1,color)
		else:
			self.game.log("Infection prevented at: "+self.name)

class PlayerRole(IntEnum):
	NULL = auto()
	CONTINGENCY_PLANNER = auto()
	DISPATCHER = auto()
	MEDIC = auto()
	OPERATIONS_EXPERT = auto()
	QUARANTINE_SPECIALIST = auto()
	RESEARCHER = auto()
	SCIENTIST = auto()
					
class Player(object):
	def __repr__(self):
		return self.playerrole.name+" Current location: "+str(self.position)+" - Cards: "+str(self.cards)
		
	def __init__(self):
		self.cards = []
		self.position = None
		self.playerrole = PlayerRole.NULL
		self.actions = {
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

	def __call__(self):
		return {
			'location': self.position,
			'role': self.playerrole.name,
			'cards': [card.name for card in self.cards]
		}

	def assign(self,game,pid):
		self.game = game
		self.pid = pid
		
	def setup(self,starting_city,role):
		self.position = starting_city
		self.playerrole = role
		if self.playerrole == PlayerRole.OPERATIONS_EXPERT:
			self.special_move = False
		self.game.player_deck.discard.extend(self.cards)
		self.cards = []
		
	def postsetup(self):
		self.move_triggers()
			
	def draw(self,amount):
		for c in range(amount):
			card = self.game.player_deck.draw()
			if card.cardtype == CardType.EPIDEMIC:
				# Increase infection counter
				self.game.infection_counter += 1
				if self.game.infection_counter == 3 or self.game.infection_counter == 5:
					self.game.infection_rate+=1
				# Infect x3 bottom card
				city_name = self.game.infection_deck.draw_bottom().name
				self.game.log(self.playerrole.name+" drew: epidemic\nEpidemic at: "+city_name)
				city = self.game.cities[city_name]
				city.infect(infection=3,color=city.color)
				# Shuffle infect discard pile
				self.game.infection_deck.intensify()
			elif card.cardtype != CardType.MISSING:
				self.game.log(self.playerrole.name+" drew: "+card.name)
				# Normal card
				self.cards.append(card)
		# Draws at end of turn, so resets Operations Expert special ability
		if self.playerrole==PlayerRole.OPERATIONS_EXPERT:
			self.special_move = True
	
	def must_discard(self):
		if self.playerrole == PlayerRole.CONTINGENCY_PLANNER:
			# TODO: Check if contingency planner has kept additional card
			return len(self.cards)>7
		else:
			return len(self.cards)>7
	
	# Card is a string with the card name
	def discard(self,card):
		valid = card in self.cards
		if valid:
			self.game.log(self.playerrole.name+" discarded: "+card)
			self.game.player_deck.discard.append(self.cards.pop(self.cards.index(card)))
		return valid
	
	# Stub function, must be implemented in child
	def request_action(self):
		return self.no_action.__name__,{}
	
	def no_action(self):
		return True
	
	# Stub function, must be implemented in child
	def request_discard(self):
		return self.cards[0]
	
	# Action is function.__name__, kwargs is a dictionary with the parameters
	# Returns if the action was successful
	def perform_action(self,action,kwargs):
		return self.actions[action](**kwargs) if action in self.actions else False
	
	# TODO: Special moves: Contingency Planner grab event ---> requires removed deck and stuff
	# TODO: Special moves: Dispatcher's friendly pawn movement
	def move_triggers(self):
		if self.playerrole == PlayerRole.MEDIC:
			self.game.medic_position = self.position
			for color in self.game.cures:
				if self.game.cures[color] and self.game.cities[self.position].disease_cubes[color]>0:
					self.game.remaining_disease_cubes[color] += self.game.cities[self.position].disease_cubes[color]
					self.game.cities[self.position].disease_cubes[color] = 0
					self.game.log("MEDIC healed "+str(color)+" at "+str(self.position))
		elif self.playerrole == PlayerRole.QUARANTINE_SPECIALIST:
			self.game.protected_cities = [self.position]
			self.game.protected_cities.extend(self.game.cities[self.position].neighbors)
	
	# Target is string object to new position
	def drive_ferry(self,target):
		valid = target in self.game.cities[self.position].neighbors
		if valid:
			self.game.log(self.playerrole.name+" drove to: "+target)
			self.position = target
			self.move_triggers()
		return valid
	
	# Target is string object to new position
	def direct_flight(self,target):
		valid = target in self.cards and self.position!=target and target in self.game.cities.keys()
		if valid:
			self.game.log(self.playerrole.name+" direct flew to: "+target)
			self.discard(target)
			self.position = target
			self.move_triggers()
		return valid
	
	# Target is string object to new position
	def charter_flight(self,target):
		valid = self.position in self.cards and self.position!=target and target in self.game.cities.keys()
		if valid:
			self.game.log(self.playerrole.name+" charter flew to: "+target)
			self.discard(self.position)
			self.position = target
			self.move_triggers()
		return valid
	
	# Target is string object to new position
	def shuttle_flight(self,target):
		valid = self.game.cities[self.position].research_station and self.position!=target and target in self.game.cities.keys() and self.game.cities[target].research_station
		if valid:
			self.game.log(self.playerrole.name+" shuttle flew to: "+target)
			self.position = target
			self.move_triggers()
		return valid
	
	# Replace is None or string of city name in which research_station will be removed
	def build_researchstation(self,replace=None):
		if replace=="none":
			replace=None
		valid = (self.position in self.cards or self.playerrole == PlayerRole.OPERATIONS_EXPERT) and not self.game.cities[self.position].research_station and (self.game.research_station_counter<6 or (replace in self.game.cities.keys() and self.game.cities[replace].research_station))
		if valid:
			self.game.log(self.playerrole.name+" built research station")
			if self.game.research_station_counter == 6:
				self.game.cities[replace].research_station = False
				self.game.log(self.playerrole.name+" removed research station at: "+replace)
			else:
				self.game.research_station_counter += 1
			if self.playerrole != PlayerRole.OPERATIONS_EXPERT:
				self.discard(self.position)
			self.game.cities[self.position].research_station = True
		return valid
	
	# Color is string object of the color name
	def treat_disease(self,color):
		valid = self.game.cities[self.position].disease_cubes[color] > 0
		if valid:
			self.game.log(self.playerrole.name+" treated: "+color)
			if self.playerrole == PlayerRole.MEDIC or self.game.cures[color]:
				self.game.remaining_disease_cubes[color] += self.game.cities[self.position].disease_cubes[color]
				self.game.cities[self.position].disease_cubes[color] = 0
			else:
				self.game.remaining_disease_cubes[color] += 1
				self.game.cities[self.position].disease_cubes[color] -= 1
		return valid
	
	# Receiver is pid number, target is string object
	def give_knowledge(self,receiver,target):
		receiver = self.game.players[receiver  % self.game.num_players]
		valid = receiver!=self and self.position==receiver.position and target in self.cards and (self.position==target or self.playerrole==PlayerRole.RESEARCHER)
		if valid:
			self.game.log(self.playerrole.name+" gave "+target+" to: "+receiver.playerrole.name)
			receiver.cards.append(self.cards.pop(self.cards.index(target)))
		return valid
	
	# Giver is pid number, target is string object
	def receive_knowledge(self,giver,target):
		giver = self.game.players[giver % self.game.num_players]
		valid = giver!=self and self.position==giver.position and target in giver.cards and (self.position==target or giver.playerrole==PlayerRole.RESEARCHER)
		if valid:
			self.game.log(self.playerrole.name+" received "+target+" from: "+giver.playerrole.name)
			self.cards.append(giver.cards.pop(giver.cards.index(target)))
		return valid
	
	# Color is a string object, chosen_cards is an array containing string objects
	def discover_cure(self,color,chosen_cards):
		valid = self.game.cities[self.position].research_station and len(chosen_cards)==(4 if self.playerrole==PlayerRole.SCIENTIST else 5) and all([(card in self.cards and self.cards[self.cards.index(card)].cardtype==CardType.CITY and self.game.cities[card].color==color) for card in chosen_cards])
		if valid:
			self.game.log(self.playerrole.name+" found cure for: "+color)
			for card in chosen_cards:
				self.discard(card)
			self.game.cures[color] = True
		return valid
	
	# Player is pid number, target_player is pid number
	def rally_flight(self,player,target_player):
		player = self.game.players[player % self.game.num_players]
		target_player = self.game.players[target_player % self.game.num_players]
		valid = self.playerrole==PlayerRole.DISPATCHER and player.position!=target_player.position
		if valid:
			self.game.log("DISPATCHER rallied "+player.playerrole.name+" to: "+target_player.playerrole.name)
			player.position = target_player.position
			player.move_triggers()
		return valid
	
	# Discard is a string of card name, target is a string to new location
	def special_charter_flight(self,discard,target):
		valid = self.playerrole==PlayerRole.OPERATIONS_EXPERT and self.special_move and self.game.cities[self.position].research_station and discard in self.cards and discard in self.game.cities.keys() and target!=self.position
		if valid:
			self.game.log(self.playerrole.name+" special charter flew to: "+target+" discarding: "+discard)
			self.special_move = False
			self.discard(discard)
			self.position = target
		return valid
	
	# TODO: Implement different event actions
	def use_event(self,event):
		pass
	
	# Might require modification later
	def available_actions(self):
		valid_cities = [city for city in self.game.cities if city!=self.position]
		actions = {}
		if self.game.turn_controller.turn_phase==TurnPhase.ACTIONS:
			actions[self.drive_ferry.__name__] = [ {'target':city} for city in self.game.cities[self.position].neighbors ]
			actions[self.direct_flight.__name__] = [ {'target':card.name} for card in self.cards if (card.cardtype==CardType.CITY and card.name!=self.position) ]
			actions[self.charter_flight.__name__] = [ {'target':city} for city in valid_cities] if self.position in self.cards else []
			actions[self.shuttle_flight.__name__] = [ {'target':city} for city in valid_cities if self.game.cities[city].research_station] if (self.game.cities[self.position].research_station and self.game.research_station_counter>1) else []
			actions[self.build_researchstation.__name__] = ([{'replace':"none"}] if self.game.research_station_counter < 6 else [{'replace':city} for city in self.game.cities if self.game.cities[city].research_station]) if ((self.position in self.cards or self.playerrole == PlayerRole.OPERATIONS_EXPERT) and not self.game.cities[self.position].research_station) else []
			actions[self.treat_disease.__name__] = [ {'color':color} for color in self.game.colors if self.game.cities[self.position].disease_cubes[color]>0 ]
			actions[self.give_knowledge.__name__] = [{'receiver':player.pid, 'target':card.name} for player in self.game.players for card in self.cards  if (player!=self and self.position==player.position and card.cardtype==CardType.CITY and (self.position==card.name or self.playerrole==PlayerRole.RESEARCHER))]
			actions[self.receive_knowledge.__name__] = [{'giver':player.pid, 'target':card.name} for player in self.game.players for card in player.cards if (player!=self and self.position==player.position and card.cardtype==CardType.CITY and (self.position==card.name or player.playerrole==PlayerRole.RESEARCHER))]
			actions[self.discover_cure.__name__] = [{'color':color,'chosen_cards':[self.cards[i].name for i in chosen_cards]} for chosen_cards in list(itertools.combinations(np.arange(len(self.cards)),4 if self.playerrole==PlayerRole.SCIENTIST else 5)) for color in self.game.colors if all([city in self.game.cities.keys() and self.game.cities[city].color==color for city in [self.cards[i].name for i in chosen_cards]])] if self.game.cities[self.position].research_station and len(self.cards)>=(4 if self.playerrole==PlayerRole.SCIENTIST else 5) else []
			actions[self.rally_flight.__name__] = [{'player':player.pid,'target_player':target.pid} for player in self.game.players for target in self.game.players if player.position!=target.position] if self.playerrole==PlayerRole.DISPATCHER else []
			actions[self.special_charter_flight.__name__] = [{'discard':card.name,'target':city} for card in self.cards for city in valid_cities if card.name in self.game.cities.keys()] if self.playerrole==PlayerRole.OPERATIONS_EXPERT and self.special_move and self.game.cities[self.position].research_station else []
		elif self.game.turn_controller.turn_phase==TurnPhase.DISCARD:
			actions[self.discard.__name__] = [{'discard':card.name} for card in self.cards]
		return actions

class TurnPhase(IntEnum):
	INACTIVE = auto()
	NEW = auto()
	ACTIONS = auto()
	DRAW = auto()
	DISCARD = auto()
	INFECT = auto()
class GameState(IntEnum):
	NOT_PLAYING = auto()
	PLAYING = auto()
	LOST = auto()
	WON = auto()

class PlayerTurn(object):
	def __init__(self,game):
		self.game = game
		self.player = None
		self.actions = 0
		self.current_player = -1
		self.current_turn = -1
		self.turn_phase = TurnPhase.INACTIVE
		self.game_state = GameState.NOT_PLAYING
	
	def setup(self, starting_player):
		self.current_player = starting_player
		self.current_turn = 1
		self.turn_phase = TurnPhase.NEW
		self.game_state = GameState.PLAYING
	
	def start_turn(self):
		valid = self.turn_phase == TurnPhase.NEW
		if valid:
			self.player = self.game.players[self.current_player]
			self.actions = 4
			self.turn_phase = TurnPhase.ACTIONS
		else:
			print("Invalid turn start, current turn phase: "+self.turn_phase.name)
	
	def do_action(self,action,kwargs):
		valid = self.turn_phase == TurnPhase.ACTIONS and action!=self.player.discard.__name__
		if valid:
			try:
				if self.player.perform_action(action,kwargs):
					self.actions -= 1
					if self.actions == 0:
						self.turn_phase = TurnPhase.DRAW
				else:
					valid = False
					print("Invalid move or something")
			except:
				print("Error, wrong function or something.")
				print(action)
				print(kwargs)
				self.turn_phase = TurnPhase.INACTIVE
				self.game.error_ocurred = True
			# TODO: Can only check if action == Cure
			self.game.eradication_check()
			if self.game.won():
				self.turn_phase = TurnPhase.INACTIVE
				self.game_state = GameState.WON
		else:
			print("Invalid do action, current turn phase: "+self.turn_phase.name)
		return valid
	
	def draw_phase(self):
		valid = self.turn_phase == TurnPhase.DRAW
		if valid:
			self.player.draw(2)
			if self.player.must_discard():
				self.turn_phase = TurnPhase.DISCARD
			else:
				self.turn_phase = TurnPhase.INFECT
		return valid
	
	def do_discard(self,discard):
		valid = self.turn_phase == TurnPhase.DISCARD
		if valid:
			if self.player.discard(discard):
				if not self.player.must_discard():
					self.turn_phase = TurnPhase.INFECT
			else:
				print("Invalid card discard")
		else:
			print("Invalid do discard, current turn phase: "+self.turn_phase.name)
		return valid
	
	def end_turn(self):
		valid = self.turn_phase == TurnPhase.INFECT
		if valid:
			for i in range(self.game.infection_rate):
				city_name = self.game.infection_deck.draw().name
				city = self.game.cities[city_name]
				city.infect(infection=1,color=city.color)
				self.outbreak_chain = []
			self.current_player = (self.current_player+1)%self.game.num_players
			if self.game.lost():
				self.turn_phase = TurnPhase.INACTIVE
				self.game_state = GameState.LOST
			else:
				self.current_turn += 1
				self.turn_phase = TurnPhase.NEW
		else:
			print("Invalid end turn, current turn phase: "+self.turn_phase.name)
		return valid

class PlayerDeck(object): 
	def __repr__(self):
		return "Expecting epidemic: "+str(1 if self.expecting_epidemic else 0)+", Next epidemic in: "+str(self.epidemic_countdown[-1])
		
	def __init__(self,cities,events):
		self.deck = []
		self.discard = []
		self.epidemic_countdown = []
		self.expecting_epidemic = False
		self.out_of_cards = False
		self.deck.extend(cities)
		self.deck.extend(events)
	
	def __call__(self):
		remaining_cards = [card.name for card in self.deck]
		remaining_cards.sort()
		return {
			'cards_left': len(self.deck),
			'deck': remaining_cards,
			'discard': [card.name for card in self.discard],
			'epidemic_countdown': self.epidemic_countdown[-1],
			'epidemic_expectation': self.expecting_epidemic
		}
	
	def presetup(self):
		# Removes epidemic cards
		self.deck.extend(self.discard)
		self.deck = [card for card in self.deck if card.cardtype != CardType.EPIDEMIC]
		self.discard = []
		self.epidemic_countdown = [len(self.deck)]
		random.shuffle(self.deck)
		
	def setup(self,epidemic_cards):
		self.out_of_cards = False
		subpiles = [[Card(name="Epidemic",cardtype=CardType.EPIDEMIC)] for i in range(epidemic_cards)]
		for index,card in enumerate(self.deck):
			subpiles[index%epidemic_cards].append(card)
		self.deck = []
		self.epidemic_countdown = []
		self.expecting_epidemic = True
		for pile in subpiles:
			random.shuffle(pile)
			self.deck.extend(pile)
			self.epidemic_countdown.append(len(pile))
			
	def draw(self):
		try:
			card = self.deck.pop()
			if card.cardtype == CardType.EPIDEMIC:
				self.expecting_epidemic = False
			self.epidemic_countdown[-1]-=1
			if self.epidemic_countdown[-1]==0:
				self.epidemic_countdown.pop()
				self.expecting_epidemic = True
		except IndexError:
			card = Card(name="",cardtype=CardType.MISSING)
			self.out_of_cards = True
		return card
	
	def remaining_cards(self,cities,colors):
		remain = {color:0 for color in colors}
		remain['event']=0
		remain['epidemic']=0
		for card in self.deck:
			remain[cities[card.name].color if card.cardtype==CardType.CITY else ("event" if card.cardtype==CardType.EVENT else "epidemic")] += 1
		return remain
	
class InfectionDeck(object):
	def __repr__(self):
		return "Possible next cards: "+str(self.known_cards)
		
	def __init__(self,cities):
		self.deck = []
		self.discard = []
		self.known_cards = []
		self.deck.extend(cities)
		
	def __call__(self):
		return {
			'known_piles': [[card.name for card in subdeck] for subdeck in self.known_cards],
			'discard': [card.name for card in self.discard]
		}
		
	def setup(self):
		self.deck.extend(self.discard)
		self.known_cards = [self.deck.copy()]
		self.discard = []
		random.shuffle(self.deck)
		
	def draw(self):
		city = self.deck.pop()
		self.known_cards[-1].remove(city)
		if len(self.known_cards[-1])==0:
			self.known_cards.pop()
		self.discard.append(city)
		return city
	
	def draw_bottom(self):
		city = self.deck.pop(0)
		self.known_cards[0].remove(city)
		self.discard.append(city)
		return city
		
	def intensify(self):
		self.known_cards.append(self.discard.copy())
		random.shuffle(self.discard)
		self.deck.extend(self.discard)
		self.discard = []

if __name__ == '__main__':
	from Players import RandomPlayer
	debug_console = True
	game = Game([RandomPlayer(),RandomPlayer()])
	game.setup()
	game.game_loop()
	