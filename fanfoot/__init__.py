from collections import namedtuple
import ConfigParser
import os.path

import fanfoot.db
import fanfoot.scoring
import fanfoot.stats

cur_dir = os.path.split(__file__)[0]

LeagueConfig = namedtuple('LeagueConfig',
                          ['label', 'kind', 'season', 'key', 'scoring'])

def conn(fpath=None, db_profile='default'):
    fanfoot.stats.clear()
    return fanfoot.db.MySQLConn(db_profile)

def find(label):
    return leagues()[label]

def leagues(config_path=None):
    if config_path is None:
        config_path = os.path.join(cur_dir, 'config.ini')

    config = ConfigParser.RawConfigParser()
    config.readfp(open(config_path))
    league_info = {}
    for label in config.sections():
        d = dict([(o, config.get(label, o)) for o in config.options(label)])
        league_info[label] = LeagueConfig(
                                 label=label,
                                 kind=config.get(label, 'kind'),
                                 season=config.get(label, 'season'),
                                 key=config.get(label, 'key'),
                                 scoring=fanfoot.scoring.create_config(d))
    return league_info

def table_csv(lst):
    lines = []
    for row in lst:
        if row is None:
            lines.append('')
        else:
            lines.append('\t'.join(map(str, row)))
    return '\n'.join(lines)

def table(lst):
    """
    Takes a list of iterables and returns them as a nicely formatted table.

    All values must be convertible to a str, or else a ValueError will
    be raised.

    N.B. I thought Python's standard library had a module that did this
    (or maybe it was Go's standard library), but I'm on an airplane and
    pydoc sucks.
    """
    pad = 2
    maxcols = []
    output = []
    first_row = True
    for row in lst:
        if row is None:
            output.append([])
            continue

        output_row = []
        for i, cell in enumerate(row):
            cell = str(cell)
            if first_row:
                maxcols.append(len(cell) + pad)
            else:
                maxcols[i] = max([maxcols[i], len(cell) + pad])
            output_row.append(cell)

        output.append(output_row)
        first_row = False

    rowsep = '-' * sum(maxcols)
    nice = []
    for i, row in enumerate(output):
        nice_row = []
        for j, cell in enumerate(row):
            nice_row.append(cell.ljust(maxcols[j]))
        nice.append(''.join(nice_row))
        if i < len(output) - 1:
            nice.append(rowsep)

    return '\n'.join(nice)
            

