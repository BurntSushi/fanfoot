from collections import namedtuple
import ConfigParser
import os.path

import fantasy.league

cur_dir = os.path.split(__file__)[0]

LeagueConfig = namedtuple('LeagueConfig', ['label', 'kind', 'season', 'key'])

def db(fpath=None):
    return fantasy.league.Conn(fpath)

def find(label):
    return leagues()[label]

def leagues(config_path=None):
    if config_path is None:
        config_path = os.path.join(cur_dir, 'config.ini')

    config = ConfigParser.RawConfigParser()
    config.readfp(open(config_path))
    league_info = {}
    for label in config.sections():
        league_info[label] = LeagueConfig(
                                 label=label,
                                 kind=config.get(label, 'kind'),
                                 season=config.get(label, 'season'),
                                 key=config.get(label, 'key'))
    return league_info

