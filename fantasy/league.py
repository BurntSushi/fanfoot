from collections import namedtuple
import os
import os.path
import sqlite3

import fantasy
import fantasy.player

_sort_positions = {
    'QB': 1,
    'RB': 2,
    'WR': 3,
    'TE': 4,
    'FLEX': 5,
    'K': 6,
    'DEF': 7,
    'BN': 8,
    'IR': 9,
}

Team = namedtuple('Team', ['lgconf', 'id', 'name'])
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
            t = Team(lgconf=lgconf, id=row['team_id'], name=row['team_name'])
            teams.append(t)
        return sorted(teams, key=lambda t: t.id)

    def teams_by_id(self, lgconf):
        d = {}
        for team in self.teams(lgconf):
            d[team.id] = team
        return d
    
    def find_team(self, lgconf, team):
        """
        If team is an integer, then the team information matching the team
        with that identifier is returned. Otherwise, it is read as a string
        and is used to search team names.
        """
        try:
            team = int(team)
            try:
                return [self.teams_by_id(lgconf)[team]]
            except KeyError:
                return []
        except ValueError:
            return self.__find_team_by_name(lgconf, team)

    def score_team(self, team, week):
        """
        Scores all active players on a team for a particular week, and
        returns the final score.
        """
        players = self.roster(team.lgconf, week, team.id, bench=False)
        if not players:
            return 0.0
        return sum([p.score() or 0.0 for p in players])

    def __find_team_by_name(self, lgconf, team_name):
        """
        Searches the list of teams for a name with a case insensitive prefix
        of team_name. If there are multiple hits, they are all returned.

        This is a helper method for find_team, which is more robust.
        """
        hits = []
        for team in self.teams(lgconf):
            if team.name.lower().startswith(team_name.lower()):
                hits.append(team)
        return hits

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
                team1=Team(lgconf=lgconf,
                           id=row['team1_id'], name=row['team1_name']),
                team2=Team(lgconf=lgconf,
                           id=row['team2_id'], name=row['team2_name']))
            matchups.append(m)
        return matchups

    def all_team_matchups(self, lgconf, team_id):
        """
        Returns a list of Matchup namedtuples corresponding to all matchups
        for a specified team.
        """
        cursor = self.__conn.execute('''
            SELECT * FROM matchup
            WHERE league_key = ? AND season = ? AND ? IN (team1_id, team2_id)
        ''', (lgconf.key, lgconf.season, team_id))
        matchups = []
        for row in cursor:
            m = Matchup(
                team1=Team(lgconf=lgconf,
                           id=row['team1_id'], name=row['team1_name']),
                team2=Team(lgconf=lgconf,
                           id=row['team2_id'], name=row['team2_name']))
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

            p = fantasy.player.create_player(
                lgconf=lgconf,
                week=row['week'],
                gsis_id=row['player_gsisid'],
                pos=row['player_pos'],
                team=row['player_team'],
                name=row['player_name'])
            players.append(p)

        def sortby_pos(p):
            pos1 = _sort_positions[p.pos]
            pos2 = _sort_positions[p.player.position]
            return (pos1, pos2, p.name)
        return sorted(players, key=sortby_pos)

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

    def get_week(self):
        """
        Returns the current week from the database.
        """
        cursor = self.__conn.execute('SELECT week FROM status LIMIT 1')
        for row in cursor:
            return row['week']
        assert False, 'Could not find week in database.'

    def update_status(self, kind, season, week):
        """
        Updates the current status of the NFL season. kind is a string of
        either PRE, REG or POST. season is a string of the current year
        of the season. week is an integer indicating the week, where the
        number '1' indicates the first round of games in a phase of the
        season (i.e., the first preseason game is in week 1, the first
        regular season game is in week 1, and the wild card round of the
        postseason is in week 1.)
        """
        self.__conn.execute('DELETE FROM status')
        self.__conn.execute('''
            INSERT INTO status
            (kind, season, week)
            VALUES
            (?, ?, ?)
        ''', (kind, season, week))
        self.commit()

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
    conn.execute('''
        CREATE TABLE status (
            kind TEXT,
            season TEXT,
            week INTEGER
        )
    ''')
    conn.commit()
    return conn


