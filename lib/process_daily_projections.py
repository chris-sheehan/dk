import numpy as np
import pandas as pd
pd.set_option('display.width', 500)

ROSTER_POSITIONS = ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'Util']
ROSTER_MAPPING = dict(
	Util = ['PG', 'SG', 'SF', 'PF', 'C'],
	G = ['PG', 'SG'],
	F = ['SF', 'PF']
	)
ROSTER = dict(PG = None, SG = None, SF = None, PF = None, C = None, G = None, F = None, Util = None)
SALARY_LIM = 50000

def get_eligible_players_for_pos(position):
	global players
	return players[player[position] == True].copy()

def roster_is_not_full(roster):
	roster_not_full = False
	for k, v in roster.iteritems():
		if v is None:
			roster_not_full = True
	return roster_not_full


players = pd.read_table('data/projections/20171022.txt')
players['pos'] = players.player.apply(lambda p: p.split()[-1])
players['player'] = players.player.apply(lambda p: ' '.join(p.split()[:-1]))

pos_set = set()
for pos in players.pos.unique():
	pos_set.update(pos.split('/'))

for pos in pos_set:
	players[pos] = players.pos.apply(lambda p: pos in p)

for pos in sorted(ROSTER_MAPPING.keys()):
	pos_group = ROSTER_MAPPING[pos]
	players[pos] = players[pos_group].max(1)

players = players[['player', 'pos', 'PG', 'SG', 'PF', 'SF', 'C', 'G', 'F', 'Util', 'fp', 'cost', 'value']]
players.sort_values('value', ascending = False, inplace = True)
players['checked'] = False

iters_lim = 50
ii = 0
salary = 0
while roster_is_not_full(ROSTER):
	ii += 1
	# pick top "value" player
	player_ix = players[~players.checked].index[0]
	top_player = players.loc[player_ix]
	print top_player.name, top_player.player
	players.loc[player_ix, 'checked'] = True

	# check if any eligible roster spots are unassigned
	player_pos = [p for p in top_player[top_player == True].index.tolist() if p in ROSTER]
	player_pos_filtered = [p for p in player_pos if ROSTER[p] is None]

	# plug into one of them (first, for now ... later will adjust for scarcity, i.. % of top "value" players with given eligibility)
	if (salary + int(top_player.cost.replace(',', ''))) < SALARY_LIM:
		if player_pos_filtered:
			player_pos_assignment = player_pos_filtered[0]
			ROSTER[player_pos_assignment] = (top_player.player, top_player.cost, top_player.fp)
			salary += int(top_player.cost.replace(',', ''))

	if ii >= iters_lim:
		break

