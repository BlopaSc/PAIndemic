# -*- coding: utf-8 -*-
"""
@author: Blopa
"""

from city_cards import city_cards
from Game import Game,Player,TurnPhase,GameState
from Players import RandomPlayer

import http.server as BaseHTTPServer
import socketserver as SocketServer

import hashlib
import json
import os
import random
import shutil
import signal
import string
import sys
import threading
import time
import traceback

debug = True
log_games = False

# Custom definitions
HOST_NAME = "127.0.0.1"
PORT_NUMBER = 31337

# Logs
errlog = sys.stdout if debug else open("server.log","w")
gameresults = open("game_results.log","a")

# Required to keep track of games and locking
games = {}
participants = {}
gamelock = threading.Lock()

# Types of computer players
computers = [RandomPlayer]

# Used to kill the server + games when Control+C on server process
def signal_handler(signal, frame):
	errlog.write("Signal - kill received\n")
	errlog.flush()
	for g in games:
		games[g].close_game()
	sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

# In charge of removing idle games (>=30 minutes)
def garbage_collector():
	while True:
		time.sleep(300)
		print("Garbage collection cycle")
		gamelock.acquire()
		gids = list(games.keys())
		t = time.time()
		for g in gids:
			if t - games[g].ping >= 1800:
				print("Removing:",g)
				try:
					# Closes game, removes it from games dict
					games[g].close_game()
					del games[g]
				except Exception:
					# No idea what this is 
					traceback.print_exc()
		gamelock.release()

# Child class special for the server
class ServerGame(Game):
	def __init__(self,gid,players,epidemic_cards=5,cities=city_cards,starting_city="atlanta",number_cubes=24):
		self.time_init = time.time()
		self.ping = self.time_init
		self.gid = gid
		super().__init__(players,epidemic_cards,cities,starting_city,number_cubes)
		if log_games:
			self.logger = open("logs/game"+gid+".log","w")
	
	def close_game(self):
		print(time.asctime() + " Closing game: "+self.gid)
		if log_games:
			self.logger.close()

# Handler for the server
class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_HEAD(self):
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		
	def do_GET(self):
		try:
			return self.perform_response()
		except Exception:
			errlog.write(traceback.format_exc())
			errlog.flush()
	
	def invalid(self,gid,ispid=False):
		return len(gid)!=16 or len([c for c in gid if c not in string.hexdigits])!=0 or ((gid not in participants) if ispid else (gid not in games))
		
	def writestring(self, s):
		self.wfile.write(s.encode("utf-8"))
	
	def ok(self,content_type="text/html"):
		self.send_response(200)
		self.send_header("Content-type", content_type)
		self.send_header("Access-Control-Allow-Credentials", "true")
		self.send_header("Access-Control-Allow-Headers", "Accept, X-Access-Token, X-Application-Name, X-Request-Sent-Time")
		self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		self.send_header("Access-Control-Allow-Origin", "*")
		self.end_headers()
	
	def send_text(self,filename):
		self.ok()
		f = open(filename,"r")
		lines = f.readlines()
		f.close()
		for line in lines:
			self.writestring(line)
	
	def perform_response(self,tvars = {}):
		game = None
		# Main page = consent page
		if not self.path or self.path == "/" or self.path.startswith("/consent"):
			self.send_text("html/consent.html")
			return
		if self.path.startswith("/tutorial"):
			self.send_text("html/tutorial.html")
			return
		if (self.path.startswith("/build/") or self.path.startswith("/images/")) and ".." not in self.path:
			fname = self.path[1:]
			if os.path.exists(fname) and os.path.isfile(fname):
				f = open(fname, "rb")
				self.send_response(200)
				self.end_headers()
				shutil.copyfileobj(f, self.wfile)
				f.close()
			else:
				self.send_response(404)
				self.end_headers()
				self.wfile.write("Not found".encode("utf8"))
			return			
		if self.path.startswith("/newgame"):
			self.ok("text/json")
			gamelock.acquire()
			pid = self.getgid()
			ai = random.choice(computers)
			# TODO: In participants save information regarding randomness selection and player roles
			participants[pid] = [ai.__name__]
			gid = self.getgid()
			game = ServerGame(gid,[Player(),ai()])
			games[gid] = game
			gamelock.release()
			game.setup()
			if game.turn_controller.current_player != 0:
				game.game_turn()
			game.turn_controller.start_turn()
			game_state = game()
			game_state.update({"gid": gid, "pid": pid})
			game_state = json.dumps(game_state,indent="\t").split('\n')	
			for line in game_state:
				self.writestring(line)
			return
		if self.path.startswith("/game"):
			gid = self.path[5:self.path.find('?')]
			gamelock.acquire()
			if gid in games:
				game = games[gid]
			else:
				print("Game not found, gid: "+gid)
				gamelock.release()
				self.send_response(400)
				self.send_header("Content-type", "text/html")
				self.end_headers()
				return
			gamelock.release()
			game.ping = time.time()
			path = self.path[self.path.find('?')+1:]
			get_dictionary = {get[:get.find("=")]: get[get.find("=")+1:] for get in path.split("&")}
			pid = get_dictionary['pid']
			del get_dictionary['pid']
			# Transforms specific parameters to int's or array where needed
			if 'receiver' in get_dictionary.keys():
				get_dictionary['receiver'] = int(get_dictionary['receiver'])
			if 'giver' in get_dictionary.keys():
				get_dictionary['giver'] = int(get_dictionary['giver'])
			if 'player' in get_dictionary.keys():
				get_dictionary['player'] = int(get_dictionary['player'])
			if 'target_player' in get_dictionary.keys():
				get_dictionary['target_player'] = int(get_dictionary['target_player'])
			if 'chosen_cards' in get_dictionary.keys():
				get_dictionary['chosen_cards'] = get_dictionary['chosen_cards'].split('-')
			# Extracts action and acts accordingly
			action = get_dictionary['action']
			del get_dictionary['action']
			if game.turn_controller.current_player == 0:
				# Player must discard
				if action == 'discard' and game.turn_controller.turn_phase==TurnPhase.DISCARD:
					game.turn_controller.do_discard(**get_dictionary)
				# Player must perform action
				elif game.turn_controller.turn_phase==TurnPhase.ACTIONS:
					game.turn_controller.do_action(action,get_dictionary)
					# If the action produces the end of action phase, then do draw step
					if game.turn_controller.turn_phase==TurnPhase.DRAW:
						# Might get the turn phase to Discard or Infect
						game.turn_controller.draw_phase()
				# Be it with the Discard phase or the Action phase, if it ends in Infect phase, perform
				if game.turn_controller.turn_phase==TurnPhase.INFECT:
					# After infection, turn phase is new
					game.turn_controller.end_turn()
			# Player receives update up to after infection phase, must request "finish_turn" for AI to execute
			elif action == 'finish_turn' and game.turn_controller.turn_phase==TurnPhase.NEW:
				game.turn_controller.start_turn()
				while game.turn_controller.turn_phase == TurnPhase.ACTIONS:
					action, kwargs = game.turn_controller.player.request_action()
					game.turn_controller.do_action(action,kwargs)
				if game.turn_controller.turn_phase==TurnPhase.DRAW:
					game.turn_controller.draw_phase()
				while game.turn_controller.turn_phase==TurnPhase.DISCARD:
					discard = game.turn_controller.player.request_discard()
					game.turn_controller.do_discard(discard)
				if game.turn_controller.turn_phase==TurnPhase.INFECT:
					game.turn_controller.end_turn()
				if game.turn_controller.turn_phase==TurnPhase.NEW:
					game.turn_controller.start_turn()
			self.ok("text/json")
			game_state = json.dumps(game(),indent="\t").split('\n')
			for line in game_state:
				self.writestring(line)
			if game.turn_controller.game_state==GameState.LOST or game.turn_controller.game_state==GameState.WON:
				# Saves game results to game_results.log
				gameresults.write(",".join([gid, pid, str(time.time() - game.time_init),*[str(param) for param in participants[pid]],game.turn_controller.game_state.name,str(sum(list(game.cures.values()))),str(sum(list(game.eradicated.values()))),str(len(game.player_deck.deck)),str(game.outbreak_counter),*[str(value) for value in game.remaining_disease_cubes.values()]])+"\n")
				# Results: gid, pid, time_taken, participants info, won/loss, cures_found, eradicated_diseases, pcards_remaining, outbreaks, disease_cubes_remaining x4
				# TODO: record player answers to survey
			return
		self.send_response(400)
		self.send_header("Content-type", "text/html")
		self.end_headers()

	def getgid(self):
		peer = str(self.connection.getpeername()) + str(time.time()) + str(os.urandom(4))
		return hashlib.sha224(peer.encode("utf8")).hexdigest()[:16]

class ThreadingHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
	# Actually processes the request by instantiating RequestHandlerClass and calling its handle() method.
	def finish_request(self, request, client_address):
		request.settimeout(30)
		# "super" can not be used because BaseServer is not created from object
		BaseHTTPServer.HTTPServer.finish_request(self, request, client_address) 

# Executed if main		
if __name__ == '__main__':
	# Creates logs folder
	if not os.path.exists("logs/"):
		os.makedirs("logs")
	# Creates server, requires ((HOST, PORT), MyTCPHandler)
	server = ThreadingHTTPServer((HOST_NAME, PORT_NUMBER), MyHandler)
	errlog.write(time.asctime() + " Server Starts - %s:%s\n" % (HOST_NAME, PORT_NUMBER))
	errlog.flush()
	# Threads the garbage collector
	t = threading.Thread(target=garbage_collector)
	# Makes it a daemon: will close abruptly on exit, doesn't counts as a thread to keep the program running
	t.daemon = True
	t.start()
	# Starts server, no idea how the exception happens
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		pass
	server.server_close()
	errlog.write(time.asctime() +  " Server Stops - %s:%s\n" % (HOST_NAME, PORT_NUMBER))
	errlog.flush()