# -*- coding: utf-8 -*-
"""
@author: Blopa
"""

import datetime
import itertools as it
import math
from multiprocessing import Process,Queue
import numpy as np
import os
import pandas as pd
import queue
import sys
import time
from Game import Game
from Heuristics import Heuristic

# Receives a seed, player_classes, heuristic_weights, num_epidemics and access to a queue of tasks (gid) and a queue to append results to (gid,result,cures,eradicated,rscounter,turn,*player_roles)
def run_simulations(seed,players_classes,heuristic_weights,num_epidemics,tasks,results):
	players = [cls() for cls in players_classes]
	game_test = Game(players,epidemic_cards=num_epidemics,log_game=False,external_log=None)
	Heuristic.set_weights(*heuristic_weights)
	while True:
		try:
			task = tasks.get_nowait()
		except queue.Empty:
			break
		else: # Useless else
			gameid = task
			game_test.setup(seed=seed*(gameid+1))
			game_test.game_loop()
			result = (
				gameid,
				game_test.game_state.name,
				sum(game_test.cures.values()), 
				sum(game_test.eradicated.values()), 
				game_test.research_station_counter, 
				game_test.current_turn, 
				tuple(player.playerrole.name for player in game_test.players)
			)
			results.put(result)

def perform_test(num_procs,num_simulations,experiment_name,seed,players_classes,heuristic_weights,num_epidemics=4,recovery=False):
	filename = 'logs/log_'+experiment_name+'.data'
	result_filename = 'logs/log_'+experiment_name+'_results.txt'
	position = 0
	results = []
	cures = np.zeros(num_simulations)
	eradicated = np.zeros(num_simulations)
	rsbuilt = np.zeros(num_simulations)
	turns = np.zeros(num_simulations)
	try:
		if not os.path.exists('logs'):
			os.mkdir('logs')
		if recovery and os.path.exists(filename):
			with open(filename,'r') as loading:
				lines = [line.split(',') for line in loading.readlines()[1:] if len(line)>0]
				results = [[int(line[0]),line[1],int(line[2]),int(line[3]),int(line[4]),int(line[5]),*line[6:]] for line in lines]
				for res in results:
					gid = res[0]
					cures[gid],eradicated[gid],rsbuilt[gid],turns[gid] = res[2:6]
				position = len(results)
			output = open(filename,'a')
			print('Continuing test: '+filename+' at '+str(position))
		else:			
			output = open(filename,'w')
			output.write('No,Result,Cures,Eradicated,RS,Turns,%s\n'%(','.join(['P%i-role'%(i) for i in range(len(players_classes))])))
			output.flush()
			print('Performing test: '+filename)
	except:
		print('Error opening file: '+filename)
		return
	procs = []
	every = max(int(num_simulations/100),1)
	task_queue = Queue()
	result_queue = Queue()
	for i in range(position,num_simulations):
		task_queue.put(i)
	t_start = time.time()
	for p in range(num_procs):
		proc = Process(target=run_simulations,args=(seed,players_classes,heuristic_weights,num_epidemics,task_queue,result_queue))
		procs.append(proc)
		proc.start()
	for n in range(position,num_simulations):
		data = result_queue.get(block=True,timeout=None)
		results.append(data)
		gameid,game_result,this_cures,this_eradicated,this_rsbuilt,this_turn,players = data
		cures[gameid] = this_cures
		eradicated[gameid] = this_eradicated
		rsbuilt[gameid] = this_rsbuilt
		turns[gameid] = this_turn
		results.sort(key = lambda x: x[0])
		for data in results[position:]:
			gameid,game_result,this_cures,this_eradicated,this_rsbuilt,this_turn,players = data
			if gameid==position:
				output.write('%i,%s,%i,%i,%i,%i,%s\n'%(gameid,game_result,this_cures,this_eradicated,this_rsbuilt,this_turn,','.join(players)))
				output.flush()
				position += 1
		if (n+1)%every==0:
			print('Completed: %.2f%%, winrate: %.2f%%'%(100*(n+1)/num_simulations,100*len(cures[cures==4])/(n+1)))
			sys.stdout.flush()
	output.close()
	won = len(cures[cures==4])
	for proc in procs:
		proc.join()
	with open(result_filename,'w') as output_results:
		tstudent = {1:12.71,10:2.228,30:2.042,60:2.000,100:1.984,1000:1.962}
		t = min(tstudent[i] for i in range(1,num_simulations+1) if i in tstudent)
		output_results.write('Tests: %i, seed: %i\n'%(num_simulations,seed))
		output_results.write('Epidemics: %i, players: %i\n'%(num_epidemics,len(players_classes)))
		output_results.write('Weight parameters: %s\n'%(str(heuristic_weights)))
		output_results.write('Time taken: %.2fs\n'%(time.time()-t_start))
		output_results.write('Average %s: %.2f +- %.3f Max: %i\n' % ('cures',cures.mean(),t*cures.std()/math.sqrt(cures.size),cures.max()))
		output_results.write('Average %s: %.2f  Max: %i\n' % ('eradicated',eradicated.mean(),eradicated.max()))
		output_results.write('Average %s: %.2f  Max: %i\n' % ('RS',rsbuilt.mean(),rsbuilt.max()))
		output_results.write('Average %s: %.2f  Max: %i  Min: %i\n' % ('turns',turns.mean(),turns.max(),turns.min()))
		output_results.write('Total %s: %i  or %.2f%%\n' % ('victories',won,100*won/num_simulations))
		output_results.write('Cures histogram: [')
		for c in range(0,int(max(cures))+1):
			output_results.write('%s%.2f'%((', ' if c>0 else ''),len(cures[cures==c])/num_simulations))
		output_results.write(']\n')
		output_results.write('Turns histogram: [')
		for t in range(int(min(turns)),int(max(turns))+1):
			output_results.write('%s%.2f'%((', ' if t>int(min(turns)) else ''),len(turns[turns==t])/num_simulations))
		output_results.write(']\n')
		output_results.flush()
	return (cures.mean(),100*won/num_simulations,eradicated.mean(),rsbuilt.mean(),turns.mean())
	
# Performs tests with each combination of parameters: paramenters is a nx7 numpy matrix with n combination of heuristic parameters
def perform_experiment(num_procs,num_simulations,experiment_name,seed,players_classes,parameters):
	exp_file = 'logs/experiment_log_'+experiment_name+'.log'
	if os.path.exists(exp_file):
		table = pd.read_csv(exp_file,sep=',')
	else:
		table = pd.DataFrame(columns=['wDistancesDiseases','wDistancesRS','wCards','wDiscard','wDiseases','wRSBuilt','wCures','curesMean','winAverage','eradicatedMean','rsBuilt','turnsMean'])
		with open(exp_file,'w') as file:
			file.write('wDistancesDiseases,wDistancesRS,wCards,wDiscard,wDiseases,wRSBuilt,wCures,curesMean,winAverage,eradicatedMean,rsBuilt,turnsMean\n')
			file.flush()
	with open(exp_file,'a') as file:
		for r in range(parameters.shape[0]):
			weights = list(parameters[r])
			if any(list(table.loc[r][:len(weights)])==weights for r in range(table.shape[0])):
				continue
			print('Processing %i: %s'%(r,str(weights)))
			now = datetime.datetime.now()
			date = '%i-%i-%i_%02i%02i'%(now.year,now.month,now.day,now.hour,now.minute)
			results = perform_test(num_procs,num_simulations,experiment_name+'_'+date,seed,players_classes,weights)
			table.loc[table.shape[0]] = [*weights,*results]
			file.write(str(weights)[1:-1]+', '+str(results)[1:-1]+'\n')
			file.flush()
	return table

# spaces: 7-tuple of linspace tuples: (min,max,num) for parameters: distancesDiseases,distancesRS,cards,discard,diseases,rsBuilt,cures
def get_parameters(spaces):
	parameters = []
	for element in it.product(*(np.linspace(t[0],t[1],t[2]) for t in spaces)):
		parameters.append(element)
	return np.array(parameters)	

if __name__=='__main__':
	from Players import PlanningPlayer
	x = perform_test(1,15,'Single',21,[PlanningPlayer,PlanningPlayer],[None for i in range(7)],recovery=True)
	print(x)
	x = perform_test(6,15,'Parallel',21,[PlanningPlayer,PlanningPlayer],[None for i in range(7)],recovery=True)
	print(x)
	pass
