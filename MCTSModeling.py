# -*- coding: utf-8 -*-
"""
@author: Blopa
"""

from Game import CardType,PlayerRole
from Heuristics import Heuristic
import copy

class MCTSModeling:
	def __init__(self,initial_state,rollouts=64):
		self.initial_state = initial_state.copy(randomize=True)
		prng = copy.deepcopy(initial_state.prng)
		self.rollouts = rollouts
		self.player_draws = []
		self.infection_draws = []
		for r in range(rollouts):
			infection_deck = copy.copy(initial_state.infection_deck)
			infection_deck.deck = initial_state.infection_deck.get_possible_deck(prng)
			infection_deck.discard = copy.copy(initial_state.infection_deck.discard)
			infection_draw = []
			infection_rate = initial_state.infection_rate
			player_deck = copy.copy(initial_state.player_deck)
			player_deck.deck = initial_state.player_deck.get_possible_deck(prng)
			player_draw = []
			for d in range(2):
				player_card = player_deck.draw()
				if player_card.cardtype == CardType.EPIDEMIC:
					if initial_state.infection_counter+1 == 3 or initial_state.infection_counter+1 == 5:
						infection_rate+=1
					infection_card = infection_deck.draw_bottom()
					infection_draw.append((infection_card,3))
					infection_deck.discard.append(infection_card)
					prng.shuffle(infection_deck.discard)
					infection_deck.deck.append(infection_deck.discard)
				elif player_card.cardtype != CardType.MISSING:
					player_draw.append(player_card)
			self.player_draws.append(player_draw)
			for i in range(infection_rate):
				infection_card = infection_deck.draw()
				infection_draw.append((infection_card,1))
			self.infection_draws.append(infection_draw)
	
	def predict(self,state):
		colors = self.initial_state.commons['colors']
		playerrole = state.players[self.initial_state.current_player].playerrole
		starting_remaining_cubes = sum(state.remaining_disease_cubes.values()) + state.infection_rate
		starting_card_distances = sum(abs((4 if playerrole==PlayerRole.SCIENTIST else 5) - state.players[self.initial_state.current_player].colors[color]) for color in colors)
		card_value = 0
		discard_value = 0
		for draw in self.player_draws:
			playercolors = copy.copy(state.players[self.initial_state.current_player].colors)
			for card in draw:
				playercolors[card.color] += 1
			discard_value += max(sum(playercolors.values()) - 7,0)
			card_value += sum(abs((4 if playerrole==PlayerRole.SCIENTIST else 5) - playercolors[color]) for color in colors)
		disease_value = 0
		for draw in self.infection_draws:
			nstate = state.copy(randomize=False,skipDraws=True)
			nstate.cities = copy.copy(state.cities)
			for card in draw:
				nstate.cities[card[0].name] = copy.copy(state.cities[card[0].name])
				nstate.cities[card[0].name].infect(game=nstate,infection=card[1],color=card[0].color,outbreak_chain=[])
			disease_value += sum(nstate.remaining_disease_cubes.values())
		totalC = Heuristic.wCards*((card_value/self.rollouts) - starting_card_distances)
		totalD = Heuristic.wDiseases*(starting_remaining_cubes - (disease_value/self.rollouts))
		totalR = Heuristic.wDiscard*((discard_value/self.rollouts)/12)
		return max(totalC + totalD + totalR, 0)

if __name__ == '__main__':
	import sys
	import time
	from Game import Game
	from Players import RandomPlayer
	game = Game([RandomPlayer(),RandomPlayer()],external_log = sys.stdout )
	game.setup()
	print("Setting up")
	t = time.time()
	mcts = MCTSModeling(game)
	print(time.time()-t)
	print("Finished mcts")
	i = mcts.infection_draws
	p = mcts.player_draws
	f = mcts.predict
	t = time.time()
	print("H =",f(game))
	print(time.time()-t)
