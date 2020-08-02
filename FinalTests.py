# -*- coding: utf-8 -*-
"""
@author: Blopa
"""

import argparse
import os
from Players import RandomPlayer,HeuristicPlayer,PlanningPlayer
from TestsConcurrent import perform_test

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("agent", type=str, help="name of the agent to use")
	parser.add_argument("-n", "--number", type=int, help="number of simulations to run", default=1000)
	parser.add_argument("-t", "--threads", type=int, help="number of threads to use", default=1)
	parser.add_argument("-s", "--seeds", type=str, help="seed values separated by commans", default="2331,31337,171717")
	args = parser.parse_args()
	
	agents = {
		'random': RandomPlayer,
		'heuristic': HeuristicPlayer,
		'planning': PlanningPlayer
	}
	
	cls = agents[args.agent.lower()]
	
	threads = args.threads
	
	seeds = [int(s) for s in args.seeds.split(',')]

	games = args.number
	
	params = [0.5, 0.5, 1, 6, 0.6, 0.6, 24]
	p2 = [cls for i in range(2)]
	p3 = [cls for i in range(3)]
	p4 = [cls for i in range(4)]
	
	players =[None,None,p2,p3,p4]
	
	init_s = 0
	init_p = 2
	init_e = 4
	
	if not os.path.exists('results'):
		os.mkdir('results')
	progress_filename = 'results/progress_register'+cls.__name__+'.log'
	output_filename = 'results/'+cls.__name__+'_Results.txt'
	
	# Load previous state if process interrupted
	try:
		with open(progress_filename,'r') as file:
			line = file.readline().split(',')
			init_s,init_p,init_e = int(line[0]),int(line[1]),int(line[2])
	except:
		pass
	print("Starting at s=%i, p=%i, e=%i"%(init_s,init_p,init_e))
	with open(output_filename,"a") as resfile:
		for s in range(init_s,len(seeds)):
			seed = seeds[s]
			for p in range(init_p,5):
				for e in range(init_e,7):
					# Update current state being process in log
					with open(progress_filename,'w') as file:
						file.write('%i,%i,%i'%(s,p,e))
					# Perform tests
					results = perform_test(num_procs=threads,num_simulations=games,experiment_name='%s_Final%ip%ie_s%i'%(cls.__name__,p,e,seed),seed=seed,players_classes=players[p],heuristic_weights=params,num_epidemics=e,recovery=True)
					# Save results
					if p==2 and e==4:
						resfile.write('Seed: '+str(seed)+'\n')
						resfile.write('Eps.\t4\t\t5\t\t6\n')
					if e==4:
						resfile.write(str(p)+'p')
					resfile.write('\t%.1f%%/%.3f'%(results[1],results[0]))
					resfile.flush()
				init_e = 4
				resfile.write('\n')
				resfile.flush()
			init_p = 2
	
	# Delete state log
	os.remove(progress_filename)
