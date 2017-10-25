import numpy as np
import pandas as pd
pd.set_option('display.width', 500)
from sklearn.linear_model import LinearRegression

"""
### Process Outline
* remove 0fps
* measure linear rel of fps/cost
* calculate supplemental_value
* pick in order of most supplemental value
* at all times, keep track of cheapest value to fill out spots w/ pos_value
* use remaining funds to upgrade lowest value spots
"""


ROSTER_POSITIONS = ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'Util']
ROSTER_MAPPING = dict(
	Util = ['PG', 'SG', 'SF', 'PF', 'C'],
	G = ['PG', 'SG'],
	F = ['SF', 'PF']
	)
ROSTER = dict(PG = None, SG = None, SF = None, PF = None, C = None, G = None, F = None, Util = None)
SALARY_LIM = 50000

def roster_is_not_full(roster):
	roster_not_full = False
	for k, v in roster.iteritems():
		if v is None:
			roster_not_full = True
	return roster_not_full

def get_reserve_required(R, df):
    reserve = 0
    for pos, v in R.iteritems():
        if v is None:
            reserve += get_cheapest_option(pos, df)
    return reserve

def get_cheapest_option(pos, df):
    return df.loc[(df.pos_value) & (df[pos]) & (~df.checked), 'cost'].min()

salary = 0
# df = pd.read_table('~/Documents/projects/dk/data/projections/20171022.txt')[['fp', 'cost', 'value']]
df = pd.read_table('~/Documents/projects/dk/data/projections/20171022.txt')
df.cost = df.cost.apply(lambda c: int(c.replace(',', '')))

df['pos'] = df.player.apply(lambda p: p.split()[-1])
df['player'] = df.player.apply(lambda p: ' '.join(p.split()[:-1]))

pos_set = set()
for pos in df.pos.unique():
	pos_set.update(pos.split('/'))

for pos in pos_set:
	df[pos] = df.pos.apply(lambda p: pos in p)

for pos in sorted(ROSTER_MAPPING.keys()):
	pos_group = ROSTER_MAPPING[pos]
	df[pos] = df[pos_group].max(1)

df = df[['player', 'pos', 'PG', 'SG', 'PF', 'SF', 'C', 'G', 'F', 'Util', 'fp', 'cost', 'value']]
df = df[df.fp > 0]


linreg = LinearRegression(fit_intercept=False)
linreg.fit(df[['cost']], df.fp)
print linreg.coef_

df['yhat'] = linreg.predict(df.cost.values.reshape(len(df), 1))
df['pos_value'] = df.fp > df.yhat
df['supp_val'] = df.fp - df.yhat
df.sort_values('supp_val', ascending = False, inplace = True)
# df.sort_values('supp_val', ascending = False).head(10)


ROSTER = dict(PG = None, SG = None, SF = None, PF = None, C = None, G = None, F = None, Util = None)
df['checked'] = False
df.sort_values('supp_val', ascending = False, inplace = True)
print 'LIM: $%s' % SALARY_LIM
iters_lim = 50
ii = 0
salary = 0
reserve = 0
while roster_is_not_full(ROSTER):
    ii += 1
    # pick top "value" player
    player_ix = df[~df.checked].index[0]
    top_player = df.loc[player_ix]
    # 	print top_player.name, top_player.player
    df.loc[player_ix, 'checked'] = True

    # check if any eligible roster spots are unassigned
    player_pos = [p for p in top_player[top_player == True].index.tolist() if p in ROSTER]
    player_pos_filtered = [p for p in player_pos if ROSTER[p] is None]

    # plug into one of them (first, for now ... later will adjust for scarcity, i.. % of top "value" df with given eligibility)
    if player_pos_filtered:
        player_pos_assignment = player_pos_filtered[0]
        tmp_reserve = get_reserve_required({k : v for k, v in ROSTER.iteritems() if k != player_pos_assignment}, df)
        if (salary + top_player.cost + tmp_reserve) <= SALARY_LIM:
            print '%s for $%s' % (top_player.player, top_player.cost)            
            ROSTER[player_pos_assignment] = dict(ix = top_player.name, name = top_player.player, cost = top_player.cost, fp = top_player.fp, value = top_player.supp_val)
            salary += top_player.cost
            print '$%s remaining.' % (SALARY_LIM - salary)
            reserve = get_reserve_required(ROSTER, df)
            print '$%s needed for reserve.\n' % reserve
            

    if ii >= iters_lim:
        break

for pos, pl in ROSTER.iteritems():
    print pos, pl.get('name')
    
print '\n%s points.' % sum([pu.get('fp') for pu in ROSTER.values()])
print 'Salary: %s' % salary


potential_upgrades = sorted(R.items(), key = lambda (pos, adict): adict.get('value'))
for pos, pu in potential_upgrades:
    # pos, pu = potential_upgrades[0]
    names = [vals.get('name') for (k, vals) in potential_upgrades]
    max_cost = SALARY_LIM  - (sum([vals.get('cost') for (k, vals) in potential_upgrades]) - pu.get('cost'))
    print max_cost
    options = df[(df.player.isin(names)==False) & df[pos] & (df.cost <= max_cost)].copy()
    if options.supp_val.max() > pu.get('value'):
        salary -= pu.get('cost')
        replacement = options.iloc[0]
        salary += replacement.cost
        ROSTER[pos] = dict(ix = replacement.name, name = replacement.player, cost = replacement.cost, fp = replacement.fp, value = replacement.supp_val)
        print pu
        print ROSTER[pos]

# No changes