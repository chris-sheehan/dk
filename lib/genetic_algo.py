import numpy as np
import pandas as pd
pd.set_option('display.width', 500)
from random import choice
from copy import deepcopy
"""
### Vars
* population = number of samples in each generation
* generations = number of times to pick best options to repopulate
* survival_rate = %/# of population that survive each generation
* mutation_rate = % chance that each position is re-drafted each generation
* num_results = top samples to output after generations

### Process Outline
* remove 0fps
* randomly draft population
* for g in generations: 
    - select top %/# per survival rate
    - with uniform probability, copy some survivors to get rebuild population
    - apply mutation rate to each survivor
* after g generations, select top num_results to return
"""

FILEPATH = '~/Documents/projects/dk/data/projections/nf_20171025.txt'
ROSTER_POSITIONS = ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'Util']
ROSTER_MAPPING = dict(
	Util = ['PG', 'SG', 'SF', 'PF', 'C'],
	G = ['PG', 'SG'],
	F = ['SF', 'PF']
	)
ROSTER = dict(PG = None, SG = None, SF = None, PF = None, C = None, G = None, F = None, Util = None)
SALARY_LIM = 50000

class Roster(object):
	SALARY_LIM = 50000
	def __init__(self, players):
		self.players = players
		self.roster = dict(PG = None, SG = None, SF = None, PF = None, C = None, G = None, F = None, Util = None)
		self.roster_not_full = True
		self.used_idx = list()
		self.salary = 0
		self.total_score = 0

	def fill_roster(self):
		for position in self.roster.keys():
			if self.roster.get(position) is None:
				reserve = self.check_reserve_required(position_exception = position)
				max_cost = self.SALARY_LIM - (self.salary + reserve)
				idx, row = self.get_any_player_at_position(position, max_cost)
				self.used_idx.append(idx)
				self.roster[position] = dict(idx = idx, player = row.player, cost = row.cost, fp = row.fp)
				self.salary += row.cost
				self.total_score += row.fp

	def reset_roster_spot(self, position):
		self.salary -= self.roster[position]['cost']
		self.total_score -= self.roster[position]['fp']
		self.used_idx.remove(self.roster[position]['idx'])
		self.roster[position] = None

	def is_not_full(self):
		for k, v in self.roster.iteritems():
			if v is None:
				self.roster_not_full = True

	def check_reserve_required(self, position_exception = None):
		reserve = 0
		for position in [pos for pos, v in self.roster.iteritems() if v is None and pos != position_exception]:
			reserve += self.get_cheapest_player_at_position(position)
		return reserve

	def get_any_player_at_position(self, position, max_cost):
		players = self.players
		idx = choice(players.loc[(players.cost <= max_cost) & (players[position]) & (players.idx.isin(self.used_idx) == False)].index.tolist())
		row = players.loc[idx]
		return idx, row

	def get_cheapest_player_at_position(self, position):
		players = self.players
		return players.loc[(players[position]) & (players.idx.isin(self.used_idx) == False), 'cost'].min()



def load_player_projections(filepath):
	# df = pd.read_table(filepath)
	df = pd.read_table(filepath)
	df.cost = df.cost.fillna('0')
	df.cost = df.cost.apply(lambda c: int(c.replace(',', '')))

	df.insert(0, 'idx', df.index)
	df['pos'] = df.player.apply(lambda p: p.split()[-1])
	df['player'] = df.player.apply(lambda p: ' '.join(p.split()[:-1]))
	df.matchup = df.matchup.apply(lambda m: m.replace(' ', ''))
	pos_set = set()
	for pos in df.pos.unique():
		pos_set.update(pos.split('/'))

	for pos in pos_set:
		df[pos] = df.pos.apply(lambda p: pos in p)

	for pos in sorted(ROSTER_MAPPING.keys()):
		pos_group = ROSTER_MAPPING[pos]
		df[pos] = df[pos_group].max(1)

	df = df[['idx', 'player', 'pos', 'matchup', 'PG', 'SG', 'PF', 'SF', 'C', 'G', 'F', 'Util', 'fp', 'cost', 'value']]
	df = df[df.fp > 0]
	return df

def load_dk_players(filepath):
	dk = pd.read_csv('data/projections/dk_20171025.csv', skiprows = 7)
	dk = dk.iloc[:, 9:]
	dk.reset_index(inplace = True, drop = True)
	# player_dict = {'%s_%s' % (row['Name + ID'], row.Salary.split()[0]) : row['Name'] for ix, row in dk.iterrows()}
	player_dict = {row['Name + ID'] : row['Name'] for ix, row in dk.iterrows()}
	return player_dict


def process_generation(rosters, last_gen = False):
	for R in rosters:
		R.fill_roster()

	# select top to survive
	rosters.sort(key = lambda R: R.total_score, reverse = True)
	print 'Top Score: %s.' % rosters[0].total_score
	survivors = rosters[:int(len(rosters) * survival_rate)]

	if not last_gen:
		# repopulate survivors with copies from other survivors
		while len(survivors) < population:
			survivors.append(deepcopy(choice(survivors)))

		# create openings from mutation rate
		for R in survivors:
			for position in R.roster.keys():
				if np.random.rand() < mutation_rate:
					R.reset_roster_spot(position)
	return survivors, rosters


def build_rosters_csv(rosters):
	rows = set()
	header = 'PG,SG,SF,PF,C,G,F,Util'
	header_list = header.split(',')
	for R in rosters:
		rows.add(','.join([str(player_dict.get(R.roster[position].get('player'))) for position in header_list]))
	with open('rosters/20171025test_upload.csv', 'w') as f:
		f.write(header)
		f.write('\n')
		for row in rows:
			f.write('%s\n' % row)
	return rows

def main():
	"""
	* population = number of samples in each generation
	* generations = number of times to pick best options to repopulate
	* survival_rate = %/# of population that survive each generation
	* mutation_rate = % chance that each position is re-drafted each generation
	* num_results = top samples to output after generations
	"""

	population = 100
	generations = 50
	survival_rate = .25
	mutation_rate = .20
	num_results = population
	generation_states = {g : None for g in range(generations)}
	
	df = load_player_projections(FILEPATH)

	rosters = [Roster(df) for _ in range(population)]
	for g in range(generations):
		last_gen = (g+1) == generations
		rosters, state = process_generation(rosters, last_gen)
		generation_states[g] = state

	results = rosters[:num_results]
	build_rosters_csv(results)