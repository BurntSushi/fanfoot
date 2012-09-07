import os
import os.path
import sqlite3

from fantasy.ffyql import yqlquery

_cur_dir = os.path.split(__file__)[0]

class Conn (object):
    def __init__(self, fpath=None):
        if fpath is None:
            fpath = os.path.join(_cur_dir, 'leagues.db')
        if not os.access(fpath, os.R_OK):
            self.__conn = _new_db(fpath)
            return
        self.__conn = sqlite3.connect(fpath)

    def load(self, week, league_keys):
        for kind, key in league_keys:
            if kind == 'yahoo':
                _load_yahoo(self.__conn, week, key)
            elif kind == 'espn':
                _load_espn(self.__conn, week, key)
            else:
                assert False, 'Unknown league key kind %s' % kind

def _new_db(fpath):
    conn = sqlite3.connect(fpath)
    conn.execute('''
        CREATE TABLE roster (
            league_key TEXT,
            team_id TEXT,
            team_name TEXT,
            week INTEGER,
            player_name TEXT,
            player_team TEXT,
            player_pos TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE matchup (
            league_key TEXT,
            week INTEGER,
            team1_id TEXT,
            team1_name TEXT,
            team2_id TEXT,
            team2_name TEXT
        )
    ''')
    conn.commit()
    return conn


def _load_yahoo(conn, week, key):
    _load_yahoo_rosters(conn, week, key)
    _load_yahoo_matchups(conn, week, key)

def _load_yahoo_rosters(conn, week, key):
    cursor = yqlquery('''
        SELECT * FROM fantasysports.teams.roster
        WHERE league_key = '%s' AND week = %d
    ''' % (key, week))
    conn.execute('''
        DELETE FROM roster
        WHERE league_key = ? AND week = ?
    ''', (key, week))
    conn.commit()
    for row in cursor.rows:
        for player in row['roster']['players']['player']:
            vals = (key, row['team_id'], row['name'], week,
                    player['name']['full'],
                    player['editorial_team_abbr'].upper(),
                    player['selected_position']['position'])
            conn.execute('''
                INSERT INTO roster
                (league_key, team_id, team_name, week,
                 player_name, player_team, player_pos)
                VALUES
                (?, ?, ?, ?, ?, ?, ?)
            ''', vals)
        conn.commit()

def _load_yahoo_matchups(conn, week, key):
    cursor = yqlquery('''
        SELECT * FROM fantasysports.leagues.scoreboard
        WHERE league_key = '%s' AND week = %d
    ''' % (key, week))
    conn.execute('''
        DELETE FROM matchup
        WHERE league_key = ? AND week = ?
    ''', (key, week))
    conn.commit()
    for matchup in cursor.rows[0]['scoreboard']['matchups']['matchup']:
        m = matchup['teams']['team']
        vals = (key, week, m[0]['team_id'], m[0]['name'],
                m[1]['team_id'], m[1]['name'])
        conn.execute('''
            INSERT INTO matchup
            (league_key, week, team1_id, team1_name, team2_id, team2_name)
            VALUES
            (?, ?, ?, ?, ?, ?)
        ''', vals)
    conn.commit()

def _load_espn(conn, week, key):
    pass

