# -*- coding: utf-8 -*-
"""
@author: Blopa
"""

from Game import Game
from Players import RandomPlayer

game_test = Game([RandomPlayer() for i in range(2)])

errors = 0
for t in range(1000000):
	if (t+1)%10000 == 0:
		print("Game: "+str(t+1))
	game_test.setup()
	game_test.game_loop()
	if game_test.error_ocurred:
		errors += 1

print("Total errors: "+str(errors))
