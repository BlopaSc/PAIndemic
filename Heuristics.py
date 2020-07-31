# -*- coding: utf-8 -*-
"""
@author: Blopa
"""

import copy
from Game import PlayerRole

class Heuristic:
	# Heuristic weights
	wDistancesDiseases = 0.5
	wDistancesRS = 0.5
	wCards = 1
	wDiscard = 6
	wDiseases = 0.6
	wRSBuilt = 0.6
	wCures = 24
	@classmethod
	def set_weights(cls,distancesDiseases=None,distancesRS=None,cards=None,discard=None,diseases=None,rsBuilt=None,cures=None):
		if distancesDiseases is not None:
			cls.wDistancesDiseases = distancesDiseases
		if distancesRS is not None:
			cls.wDistancesRS = distancesRS
		if cards is not None:
			cls.wCards = cards
		if discard is not None:
			cls.wDiscard = discard
		if diseases is not None:
			cls.wDiseases = diseases
		if rsBuilt is not None:
			cls.wRSBuilt = rsBuilt
		if cures is not None:
			cls.wCures = cures

	@classmethod
	def get_weights(cls):
		return (cls.wDistancesDiseases,cls.wDistancesRS,cls.wCards,cls.wDiscard,cls.wDiseases,cls.wRSBuilt,cls.wCures)

	@classmethod
	def heuristic(cls,game,find_diseases=False,find_rs=False):
		colors = game.commons['colors']
		disease_cubes = game.commons['number_cubes']*len(colors) - sum(game.remaining_disease_cubes.values())
		city_distances = game.distances
		distances_diseases = 0
		distances_rs = 0
		remaining = copy.copy(game.player_deck.colors)
		for player in game.players:
			minimum = len(city_distances)
			if find_diseases:
				distances_diseases += sum(game.cities[player.position].disease_cubes.values())
				for city_name in game.cities:
					distances_diseases += city_distances[player.position][city_name]*sum(game.cities[city_name].disease_cubes.values())
			if find_rs:
				for city_name in game.cities_rs:
					if minimum>city_distances[player.position][city_name]:
						minimum = city_distances[player.position][city_name]
				distances_rs += minimum
			for color in colors:
				remaining[color] += player.colors[color]
		# Distances of weighted distances to infected cities + distance to rs
		distances = cls.wDistancesDiseases*((distances_diseases/disease_cubes) if disease_cubes>0 else 0) + cls.wDistancesRS*distances_rs
		# Value of cards in players hands increases with grouping
		cards = cls.wCards*sum(min(abs((4 if player.playerrole==PlayerRole.SCIENTIST else 5) - player.colors[color]) for player in game.players) for color in colors if not game.cures[color])
		# Discarded card values increasing with less remaining
		discard = cls.wDiscard*sum((not game.cures[color])*((12-remaining[color])/12) for color in colors)
		# Disease cubes in the world
		diseases = cls.wDiseases*disease_cubes
		# Value of research stations estimated: total distances / 48*47
		rs_building = cls.wRSBuilt*(game.total_distances/2256)*(game.commons['max_turns']-game.current_turn)/game.commons['max_turns']
		# Value of cures
		cures = cls.wCures*(4 - sum(game.cures.values()))
		# Value cards in discard
		return distances + diseases + cards + rs_building + cures + discard
