from collections import namedtuple
import os
import os.path
import sqlite3

import nflgame

import fantasy

_sort_positions = {
    'QB': 1,
    'RB': 2,
    'WR': 3,
    'TE': 4,
    'FLEX': 5,
    'K': 6,
    'DEF': 7,
    'BN': 8,
}

Player = namedtuple('Player', ['player', 'pos', 'team', 'name'])
Team = namedtuple('Team', ['id', 'name'])
Matchup = namedtuple('Matchup', ['team1', 'team2'])

class Conn (object):
    def __init__(self, fpath=None):
        if fpath is None:
            fpath = os.path.join(fantasy.cur_dir, 'leagues.db')
        if not os.access(fpath, os.R_OK):
            self.__conn = _new_db(fpath)
        else:
            self.__conn = sqlite3.connect(fpath)
        self.__conn.row_factory = sqlite3.Row

    def teams(self, lgconf):
        """
        Returns a list of Team namedtuples for a particular league.
        """
        cursor = self.__conn.execute('''
            SELECT * FROM roster
            WHERE league_key = ? AND season = ?
            GROUP BY team_id
            ORDER BY week DESC
        ''', (lgconf.key, lgconf.season))
        teams = []
        for row in cursor:
            t = Team(id=row['team_id'], name=row['team_name'])
            t.__str__ = lambda self: '%s (%d)' % (t.name, t.id)
            teams.append(t)
        return sorted(teams, key=lambda t: t.id)

    def matchups(self, lgconf, week):
        """
        Returns a list of Matchup namedtuples for a week of a league.
        """
        cursor = self.__conn.execute('''
            SELECT * FROM matchup
            WHERE league_key = ? AND season = ? AND week = ?
        ''', (lgconf.key, lgconf.season, week))
        matchups = []
        for row in cursor:
            m = Matchup(
                team1=Team(id=row['team1_id'], name=row['team1_name']),
                team2=Team(id=row['team2_id'], name=row['team2_name']))
            matchups.append(m)
        return matchups

    def roster(self, lgconf, week, team_id, bench=False):
        """
        Returns a list of Player namedtuples for a team in a particular 
        matchup.
        """
        cursor = self.__conn.execute('''
            SELECT * FROM roster
            WHERE league_key = ? AND season = ? AND week = ? AND team_id = ?
        ''', (lgconf.key, lgconf.season, week, team_id))
        players = []
        for row in cursor:
            if not bench and row['player_pos'] == 'BN':
                continue

            pid = row['player_gsisid']
            if pid == '0' or pid not in nflgame.players:
                player_info = None
            else:
                player_info = nflgame.players[pid]

            p = Player(
                player=player_info,
                pos=row['player_pos'],
                team=row['player_team'],
                name=row['player_name'])
            players.append(p)
        return sorted(players, key=lambda p: _sort_positions[p.pos])

    def add_roster(self, lgconf, team_id, team_name,
                   week, player_gsisid, player_name, player_team, player_pos):
        vals = (lgconf.key, lgconf.season, int(team_id), team_name, int(week),
                player_gsisid, player_name, player_team, player_pos)
        self.__conn.execute('''
            INSERT INTO roster
            (league_key, season, team_id, team_name, week,
             player_gsisid, player_name, player_team, player_pos)
            VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', vals)

    def delete_rosters(self, lgconf, week):
        self.__conn.execute('''
            DELETE FROM roster
            WHERE league_key = ? AND season = ? AND week = ?
        ''', (lgconf.key, lgconf.season, week))

    def add_matchup(self, lgconf, week,
                    team1_id, team1_name, team2_id, team2_name):
        vals = (lgconf.key, lgconf.season, int(week),
                int(team1_id), team1_name, int(team2_id), team2_name)
        self.__conn.execute('''
            INSERT INTO matchup
            (league_key, season, week,
             team1_id, team1_name, team2_id, team2_name)
            VALUES
            (?, ?, ?, ?, ?, ?, ?)
        ''', vals)

    def delete_matchups(self, lgconf, week):
        self.__conn.execute('''
            DELETE FROM matchup
            WHERE league_key = ? AND season = ? AND week = ?
        ''', (lgconf.key, lgconf.season, week))

    def commit(self):
        self.__conn.commit()

def _new_db(fpath):
    conn = sqlite3.connect(fpath)
    conn.execute('''
        CREATE TABLE roster (
            league_key TEXT,
            season TEXT,
            team_id INTEGER,
            team_name TEXT,
            week INTEGER,
            player_gsisid TEXT,
            player_name TEXT,
            player_team TEXT,
            player_pos TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE matchup (
            league_key TEXT,
            season TEXT,
            week INTEGER,
            team1_id INTEGER,
            team1_name TEXT,
            team2_id INTEGER,
            team2_name TEXT
        )
    ''')
    conn.commit()
    return conn


