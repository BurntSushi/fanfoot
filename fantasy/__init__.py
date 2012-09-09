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

def table(lst):
    """
    Takes a list of iterables and returns them as a nicely formatted table.

    All values must be convertible to a str, or else a ValueError will
    be raised.

    N.B. I thought Python's standard library had a module that did this
    (or maybe it was Go's standard library), but I'm on an airplane and
    pydoc sucks.
    """
    maxcols = []
    output = []
    first_row = True
    for row in lst:
        output_row = []
        for i, cell in enumerate(row):
            cell = str(cell)
            if first_row:
                maxcols.append(len(cell))
            else:
                maxcols[i] = max([maxcols[i], len(cell)])
            output_row.append(cell)

        output.append(output_row)
        first_row = False

    nice = []
    for row in output:
        nice_row = []
        for i, cell in enumerate(row):
            nice_row.append(cell.ljust(maxcols[i] + 2))
        nice.append(''.join(nice_row))

    return '\n'.join(nice)
            

