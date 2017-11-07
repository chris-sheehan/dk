
import pandas as pd
import datetime
import requests
from bs4 import BeautifulSoup

NUMBERFIRE_URL = "http://www.numberfire.com/nba/daily-fantasy/daily-basketball-projections"
OMIT_CLASSES = ('', 'cta', 'active', 'left-aligned', 'right-aligned')

FIELD_SORT = ["player", "position", "matchup", "fp", "cost", "value", "min", "pts", "reb", "ast", "stl", "blk", "tov"]
FIELD_CLASS_MAPPING = dict(
	player = dict(func = get_player_name),
	position = dict(span = {'class' : 'player-info--position'}),
	matchup = dict(span = {'class' : 'team-player__team'}),
	fp = dict(td = {'class' : 'fp'}),
	cost = dict(td = {'class' : 'cost'}),
	value = dict(td = {'class' : 'value'}),
	min = dict(td = {'class' : 'min'}),
	pts = dict(td = {'class' : 'pts'}),
	reb = dict(td = {'class' : 'reb'}),
	ast = dict(td = {'class' : 'ast'}),
	stl = dict(td = {'class' : 'stl'}),
	blk = dict(td = {'class' : 'blk'}),
	tov = dict(td = {'class' : 'to'})
)

def get_tag_classes(tag):
	try:
		classes = [c for c in tag.attrs.get('class') if c not in OMIT_CLASSES]
		tag_class = ';'.join(classes)
	except IndexError:
		tag_class = None
	return tag_class

def parse_row(row):
	player = dict()
	for fld, mapping in FIELD_CLASS_MAPPING.iteritems():
		for tag, params in mapping.iteritems():
			if tag == 'func':
				val = params(row)
			else:
				val = row_tag_attr(row, tag, params)
			print fld, tag, params, val
			player[fld] = val
	return player

def row_tag_attr(row, tag, params):
	try:
		val = row.find(tag, **params).text.strip()
	except AttributeError:
		val = ''
	return val

def get_player_name(row):
	try:
		name = row.find('a', {'class' : 'full'}).text.strip()
	except AttributeError:
		name = ''
	return name

resp = requests.get(NUMBERFIRE_URL)
html = resp.text
soup = BeautifulSoup(html, 'html.parser')

stat_table = soup.find('tbody', {'class' : 'stat-table__body'})
stat_rows = stat_table.findAll('tr')

players = list()
for row in stat_rows:
	player = dict(parse_row(row))
	players.append(player)

save_as = "nf_%s.txt" % datetime.date.today().strftime('%Y%m%d')
df = pd.DataFrame.from_records(players)[FIELD_SORT]
df.to_csv()

