# -*- coding: utf-8 -*-
"""
@author: Blopa
"""

from city_cards import city_cards
from Game import Game,Player,PlayerRole,TurnPhase,GameState
from Players import RandomPlayer,HeuristicPlayer,PlanningPlayer

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

if any(arg=='-s' for arg in sys.argv):
	print("Running in server mode")
	# Google cloud computing
	HOST_NAME = "0.0.0.0"
	PORT_NUMBER = 80
	debug = False
	
if any(arg=='-l' for arg in sys.argv):
	print("Logging games")
	log_games = True
	
questionnaire_file = "Questionnaire.txt"
questionnaire = {}
if os.path.exists(questionnaire_file):
	with open(questionnaire_file) as file:
		lines = [line.replace('\n','') for line in file.readlines() if len(line)>0]
		for line in lines:
			if not line.startswith('-') and not line.startswith('#'):
				current_section = {'description': line, 'questions': []}
				questionnaire[str(len(questionnaire))] = current_section
			elif line.startswith('#'):
				current_question = {'question': line.replace('# ',''), 'answers': []}
				current_section['questions'].append(current_question)
			elif line.startswith('-'):
				current_question['answers'].append(line.replace('- ',''))

# Required to keep track of games and locking
games = {}
participants = {}
finished_games = []
gamelock = threading.Lock()

# Due to limitations with the number of participants less combinations will be used
# Types of computer players
computers = [PlanningPlayer]
roles = [
		[PlayerRole.SCIENTIST,PlayerRole.MEDIC],
		 [PlayerRole.SCIENTIST,PlayerRole.RESEARCHER],
		 [PlayerRole.SCIENTIST,PlayerRole.QUARANTINE_SPECIALIST],
		 [PlayerRole.MEDIC,PlayerRole.RESEARCHER],
		 [PlayerRole.MEDIC,PlayerRole.QUARANTINE_SPECIALIST],
		 [PlayerRole.RESEARCHER,PlayerRole.QUARANTINE_SPECIALIST]
	 ]
seeds = [6, 7, 13, 17, 21, 512, 777]

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
					# Closes game
					games[g].close_game()
					# Removes it from games dict
					del games[g]
				except Exception:
					# No idea what this is 
					traceback.print_exc()
		gamelock.release()

# Child class special for the server
class ServerGame(Game):
	def __init__(self,gid,players,epidemic_cards=4,cities=city_cards,starting_city="atlanta",number_cubes=24):
		self.time_init = time.time()
		self.ping = self.time_init
		self.gid = gid
		super().__init__(players,epidemic_cards,cities,starting_city,number_cubes,external_log=open("logs/game"+gid+".log","w") if log_games else None)
	
	def close_game(self,save=False):
		print(time.asctime() + " Closing game: "+self.gid)
		if log_games:
			self.commons['logger'].close()
			if not save:
				os.remove("logs/game"+self.gid+".log")

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
		if not self.path or self.path == "/" or self.path.startswith("/consent") or self.path.startswith("/?"):
			self.send_text("html/consent.html")
			return
		if self.path.startswith("/tutorial"):
			self.send_text("html/tutorial.html")
			return
		if self.path.startswith("/pandemic"):
			self.send_text("html/pandemic.html")
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
		if self.path.startswith("/newgame") or self.path.startswith("/renewgame"):
			self.ok("text/json")
			gamelock.acquire()
			pid = self.getgid() if self.path.startswith("/newgame") else self.path[10:]
			gorder = participants[pid][0]+1 if pid in participants else 0
			ai = random.choice(computers)
			role = random.choice(roles)
			seed = random.choice(seeds)
			random.shuffle(role)
			participants[pid] = [gorder,ai.__name__,str(seed),role[0].name,role[1].name]
			gid = self.getgid()
			game = ServerGame(gid,[Player(),ai()])
			games[gid] = game
			gamelock.release()
			game.setup(seed=seed,players_roles=role)
			game.game_advance()
			game_state = game()
			game_state.update({"gid": gid, "pid": pid})
			game_state["game_log"] = game_state["game_log"][game_state["game_log"].index("Setting game up"):]
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
				self.writestring("Error")
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
			if game.current_player == 0:
				# Player must discard
				if action == 'discard' and game.turn_phase==TurnPhase.DISCARD:
					game.do_discard(**get_dictionary)
				# Player must perform action
				elif game.turn_phase==TurnPhase.ACTIONS:
					game.do_action(action,get_dictionary)
				game.game_advance()
			# Player receives update up to after infection phase, must request "waiting" for AI to execute
			else:
				while game.current_player!=0 and game.turn_phase == TurnPhase.ACTIONS:
					action, kwargs = game.players[game.current_player].request_action(game)
					game.do_action(action,kwargs)
				game.game_advance()
				while game.current_player!=0 and game.turn_phase==TurnPhase.DISCARD:
					discard = game.players[game.current_player].request_discard(game)
					game.do_discard(discard)
				game.game_advance()
			self.ok("text/json")
			game_state = json.dumps(game(),indent='\t').split('\n')
			for line in game_state:
				self.writestring(line)
			if game.game_state==GameState.LOST or game.game_state==GameState.WON:
				# Saves game results to game_results.log
				gameresults.write(",".join([
						gid,
						pid,
						str(time.time() - game.time_init),
						game.game_state.name,
						str(game.current_turn),
						str(sum(list(game.cures.values()))),
						str(sum(list(game.eradicated.values()))),
						str(game.player_deck.remaining),
						str(game.outbreak_counter),
						*[str(game.remaining_disease_cubes[color]) for color in ['red','yellow','blue','black']],
						*[str(param) for param in participants[pid]]
					])+"\n"
				)
				gameresults.flush()
				game.close_game(save=True)
				gamelock.acquire()
				del games[gid]
				finished_games.append(gid)
				gamelock.release()
			return
		if self.path.startswith("/reqsurvey"):
			self.ok("text/json")
			for line in json.dumps(questionnaire,indent='\t').split('\n'):
				self.writestring(line)
			return
		if self.path.startswith("/survey"):
			gid = self.path[7:self.path.find('?')]
			gamelock.acquire()
			valid = gid in finished_games
			if valid:
				finished_games.remove(gid)
			else:
				print("Finished game not found, gid: "+gid)
				gamelock.release()
				self.send_response(400)
				self.send_header("Content-type", "text/html")
				self.end_headers()
				self.writestring("Error")
				return
			gamelock.release()
			path = self.path[self.path.find('?')+1:]
			get_dictionary = {get[:get.find("=")]: get[get.find("=")+1:] for get in path.split("&")}
			pid = get_dictionary['pid']
			del get_dictionary['pid']
			answers = ['-1' for q in range(sum(len(questionnaire[section]['questions']) for section in questionnaire))]
			for key in get_dictionary:
				answers[int(key[1:])] = get_dictionary[key]
			gamesurvey.write(','.join([gid,pid] + answers) + '\n')
			gamesurvey.flush()
			self.ok()
			self.writestring("Thanks!")
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
	if not os.path.exists("results/"):
		os.makedirs("results")
	# Logs
	elog_name = "results/server.log"
	rlog_name = "results/game_results.log"
	slog_name = "results/game_survey.log"
	errlog = sys.stdout if debug else open(elog_name,"w")
	if os.path.exists(rlog_name):
		gameresults = open(rlog_name,"a")
	else:
		gameresults = open(rlog_name,"w")
		gameresults.write('gid,pid,time_taken,result,game_turn,cures_discovered,eradicated_diseases,pcards_remaining,outbreaks,dcubes_red,dcubes_yellow,dcubes_blue,dcubes_black,gorder,AI,seed,roleH,roleC\n')
		gameresults.flush()
	if os.path.exists(slog_name):
		gamesurvey = open(slog_name,"a")
	else:
		gamesurvey = open(slog_name,"w")
		gamesurvey.write(','.join(['gid','pid']+[question['question'] for section in questionnaire for question in questionnaire[section]['questions']]) +'\n')
		gamesurvey.flush()
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