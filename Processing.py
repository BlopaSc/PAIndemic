# -*- coding: utf-8 -*-
"""
@author: Blopa
"""

import matplotlib.pyplot as plt
import math
import numpy as np
import pandas as pd
import sys

seeds = [31337, 2331, 171717]
players = [2,3,4]
epidemics = [4,5,6]

ai = "PlanningPlayer"

# confidence interval
z = 1.96

data = {}
for player in players:
	for epidemic in epidemics:
		data[(player,epidemic)] = pd.concat([pd.read_csv("logs/%s/log_%s_Final%ip%ie_s%i.data" % (ai,ai,player,epidemic,seed)) for seed in seeds],ignore_index=True)
		merge_col = []
		for i in range(len(data[(player,epidemic)])):
			roles = [data[(player,epidemic)]['P%i-role'%(p)][i][0] for p in range(player)]
			roles.sort(reverse=True)
			merge_col.append("-".join(roles))
		data[(player,epidemic)]=data[(player,epidemic)].drop(columns=['No']+['P%i-role'%(p) for p in range(player)])
		data[(player,epidemic)].insert(5,"Roles",merge_col)
		
max_error = 0
for player in players:
	for epidemic in epidemics:
		n = data[(player,epidemic)]['Cures'].count()
		p = (data[(player,epidemic)]['Cures']==4).sum()/n
		max_error = max(max_error,100*z*math.sqrt(p*(1-p)/n))
		sys.stdout.write('& %.2f\\%% ' % (100*p))
	sys.stdout.write('\n')
sys.stdout.write("Max error: %.2f\\%%\n"%(max_error))

max_error = 0
for player in players:
	for epidemic in epidemics:
		n = data[(player,epidemic)]['Cures'].count()
		p = data[(player,epidemic)]['Cures'].sum()/n
		s = data[(player,epidemic)]['Cures'].std()
		max_error= max(max_error, z*s/math.sqrt(n))
		sys.stdout.write('& %.2f ' % (p))
	sys.stdout.write('\n')
sys.stdout.write("Max error: %.2f\\%%\n"%(max_error))

winrates = []
labels = []
for epidemic in epidemics:
	wins = []
	for player in players:
		roles = list(data[(player,epidemic)]['Roles'].unique())
		roles.sort(reverse=True)
		for role in roles:
			subdata = data[(player,epidemic)][data[(player,epidemic)]['Roles']==role]
			w = (subdata['Cures']==4).sum()
			n = subdata['Cures'].count()
			wins.append(100*w/n)
			if epidemic==4:
				labels.append(role)
				sys.stdout.write("Win rate for %s: %.2f%% over %i games\n"%(role,100*w/n,n))
	winrates.append(wins)
			
X = np.arange(len(labels))

fig = plt.figure()
ax = fig.add_axes([0,0,1,1])
ax.set_ylabel('Win rate (%)')
ax.set_xlabel('Role combinations')
ax.set_xticks(X)
ax.set_xticklabels(labels, rotation=-45)
ax.bar(X, winrates[0], color = 'b', width = 0.6)
ax.bar(X, winrates[1], color = 'g', width = 0.5)
ax.bar(X, winrates[2], color = 'r', width = 0.4)
ax.legend(['4 epidemics','5 epidemics','6 epidemics'])

#fig.savefig('Winrate-roles.png')

