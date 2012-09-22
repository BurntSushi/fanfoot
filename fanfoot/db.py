from collections import namedtuple
import ConfigParser
import os
import os.path
import sqlite3
import time

import MySQLdb as mysql

import fanfoot
import fanfoot.player
import fanfoot.stats

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

Game = namedtuple('Game',
                  ['game_id', 'week', 'home', 'away',
                   'score_home', 'score_away', 'time', 'playing'])
Team = namedtuple('Team', ['lgconf', 'id', 'name'])
Matchup = namedtuple('Matchup', ['team1', 'team2'])


class Stats (object):
    def __init__(self):
        self._stats = {}

    def _include_stat(self, k, v):
        self.__dict__[k] = v
        self._stats[k] = v

    def __getattr__(self, attr):
        return 0


class PlayStats (Stats):
    def __init__(self, game_id, week, play_id, team, home, desc, note, down,
                 yards_togo, time, yardline, timeline):
        super(PlayStats, self).__init__()

        self.game_id = game_id
        self.week = week
        self.play_id = play_id
        self.team = team
        self.home = home == 1
        self.desc = desc
        self.note = note
        self.down = down
        self.yards_togo = yards_togo
        self.time = time
        self.yardline = yardline
        self.timeline = timeline


class PlayerStats (Stats):
    def __init__(self, game_id, week, play_id, player_name, home):
        super(PlayerStats, self).__init__()

        self.game_id = game_id
        self.week = week
        self.player_id = play_id
        self.player_name = player_name
        self.home = home == 1


class Conn (object):
    def teams(self, lgconf):
        """
        Returns a list of Team namedtuples for a particular league.
        """
        cursor = self.execute('''
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
        return sum([p.computed_score or 0.0 for p in players])

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
        cursor = self.execute('''
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
        cursor = self.execute('''
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
        cursor = self.execute('''
            SELECT * FROM roster
            WHERE league_key = ? AND season = ? AND week = ? AND team_id = ?
        ''', (lgconf.key, lgconf.season, week, team_id))
        players = []
        for row in cursor:
            if not bench and row['player_pos'] == 'BN':
                continue

            p = fanfoot.player.create_player(
                db=self,
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
        self.execute('''
            INSERT INTO roster
            (league_key, season, team_id, team_name, week,
             player_gsisid, player_name, player_team, player_pos)
            VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', vals)

    def delete_rosters(self, lgconf, week):
        self.execute('''
            DELETE FROM roster
            WHERE league_key = ? AND season = ? AND week = ?
        ''', (lgconf.key, lgconf.season, week))

    def add_matchup(self, lgconf, week,
                    team1_id, team1_name, team2_id, team2_name):
        vals = (lgconf.key, lgconf.season, int(week),
                int(team1_id), team1_name, int(team2_id), team2_name)
        self.execute('''
            INSERT INTO matchup
            (league_key, season, week,
             team1_id, team1_name, team2_id, team2_name)
            VALUES
            (?, ?, ?, ?, ?, ?, ?)
        ''', vals)

    def delete_matchups(self, lgconf, week):
        self.execute('''
            DELETE FROM matchup
            WHERE league_key = ? AND season = ? AND week = ?
        ''', (lgconf.key, lgconf.season, week))

    def get_week(self):
        """
        Returns the current week from the database.
        """
        cursor = self.execute('SELECT week FROM status LIMIT 1')
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
        self.execute('DELETE FROM status')
        self.execute('''
            INSERT INTO status
            (kind, season, week)
            VALUES
            (?, ?, ?)
        ''', (kind, season, week))
        self.commit()

    def add_score(self, lgconf, week, player):
        vals = (
            lgconf.key,
            lgconf.season,
            week,
            player.playerid,
            player.name,
            player.score(),
        )
        self.execute('''
            REPLACE INTO score
                (league_key, season, week, gsis_id, player_name, score)
            VALUES
                (?, ?, ?, ?, ?, ?)
        ''', vals)

    def scores(self, lgconf, week):
        cursor = self.execute('''
            SELECT * FROM score
            WHERE
                league_key = ?
                AND season = ?
                AND week = ?
        ''', (lgconf.key, lgconf.season, week))

        ret = {}
        for row in cursor:
            ret[row['gsis_id']] = row['score']
        return ret

    def compute_scores(self, week):
        for lgconf in fanfoot.leagues().itervalues():
            for team in self.teams(lgconf):
                players = self.roster(lgconf, week, team.id, bench=True)
                if not players:
                    continue
                for p in players:
                    self.add_score(lgconf, week, p)

    def add_game(self, week, game):
        vals = (
            game.eid,
            week,
            game.home,
            game.away,
            game.score_home,
            game.score_away,
            str(game.time),
        )
        self.execute('''
            REPLACE INTO game
                (game_id, week, home, away, score_home, score_away, time)
            VALUES
                (?, ?, ?, ?, ?, ?, ?)
        ''', vals)

        for play in game.drives.plays():
            self.add_play(week, game.eid, play)
        for player in game.max_player_stats():
            self.add_player(week, game.eid, player)

        self.commit()

    def games(self, week):
        cursor = self.execute('''
            SELECT * FROM game WHERE week = ?
        ''', (week,))

        ret = {}
        for row in cursor:
            ret[row['game_id']] = self._new_game(row)
        return ret

    def game(self, week, team):
        cursor = self.execute('''
            SELECT * FROM game WHERE week = ? AND ? in (home, away)
        ''', (week, team))
        return self._new_game(cursor.fetchone())

    def game_by_id(self, game_id):
        cursor = self.execute('''
            SELECT * FROM game WHERE game_id = ?
        ''', (game_id,))
        return self._new_game(cursor.fetchone())

    def _new_game(self, row):
        if row is None:
            return None

        playing = 'pregame' not in row['time'].lower() \
                  and 'final' not in row['time'].lower()
        g = Game(row['game_id'], row['week'], row['home'], row['away'],
                 row['score_home'], row['score_away'],
                 row['time'], playing)
        return g

    def add_play(self, week, game_id, play):
        existing = fanfoot.stats.all_plays(self, game_id)
        if (game_id, int(play.playid)) in existing:
            vals = (
                play.desc,
                play.note,
                play.down,
                play.yards_togo,
                str(play.time),
                play.data['yrdln'],
                game_id,
                play.playid,
            )
            self.execute('''
                DELETE FROM play_stat WHERE game_id = ? AND play_id = ?
            ''', (game_id, play.playid))
            self.execute('''
                UPDATE play
                SET
                    descript = ?, note = ?, down = ?, yards_togo = ?,
                    time = ?, yardline = ?
                WHERE
                    game_id = ? AND play_id = ?
            ''', vals)
        else:
            vals = (
                game_id,
                week,
                play.playid,
                play.team,
                1 if play.home else 0,
                play.desc,
                play.note,
                play.down,
                play.yards_togo,
                str(play.time),
                play.data['yrdln'],
                int(time.time()),
            )
            self.execute('''
                INSERT INTO play
                    (game_id, week, play_id, team, home, descript, note, down,
                     yards_togo, time, yardline, timeline)
                VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', vals)

        for k, v in play._stats.iteritems():
            vals = (game_id, play.playid, k, v)
            self.execute('''
                INSERT INTO play_stat
                    (game_id, play_id, stat, value)
                VALUES
                    (?, ?, ?, ?)
            ''', vals)

    def plays(self, week):
        cursor = self.execute('''
            SELECT * FROM play
            LEFT JOIN
                play_stat
            ON
                play.game_id = play_stat.game_id
                AND play.play_id = play_stat.play_id
            WHERE
                play.week = ?
        ''', (week,))

        ret = {}
        for row in cursor:
            key = (row['game_id'], row['play_id'])
            if key not in ret:
                p = PlayStats(row['game_id'], row['week'], row['play_id'],
                              row['team'], row['home'], row['descript'],
                              row['note'], row['down'], row['yards_togo'],
                              row['time'], row['yardline'], row['timeline'])
                ret[key] = p
            else:
                p = ret[key]
            p._include_stat(row['stat'], row['value'])

        return sorted(ret.itervalues(), reverse=True,
                      key=lambda p: p.play_id)

    def add_player(self, week, game_id, player):
        toadd = {}
        for k, v in player._stats.iteritems():
            toadd[k] = v
        toadd['twoptm'] = player.twoptm
        toadd['twopta'] = player.twopta

        for k, v in toadd.iteritems():
            vals = (
                game_id,
                week,
                player.playerid,
                player.name,
                1 if player.home else 0,
                k,
                v,
            )
            self.execute('''
                REPLACE INTO player_stat
                    (game_id, week, player_id, player_name, home, stat, value)
                VALUES
                    (?, ?, ?, ?, ?, ?, ?)
            ''', vals)

    def players(self, week):
        cursor = self.execute('''
            SELECT * FROM player_stat WHERE week = ?
        ''', (week,))

        ret = {}
        for row in cursor:
            if row['player_id'] not in ret:
                p = PlayerStats(row['game_id'], row['week'], row['player_id'],
                                row['player_name'], row['home'])
                ret[row['player_id']] = p
            else:
                p = ret[row['player_id']]
            p._include_stat(row['stat'], row['value'])
        return ret

    def commit(self):
        self._conn.commit()


class SQLiteConn (Conn):
    def __init__(self, fpath=None):
        if fpath is None:
            fpath = os.path.join(fanfoot.cur_dir, 'leagues.db')

        initial = not os.access(fpath, os.R_OK)
        self._conn = sqlite3.connect(fpath)
        self._conn.row_factory = sqlite3.Row

        if initial:
            _new_sqlite_db(self)

    def execute(self, sql, vals=None):
        return self._conn.execute(sql, vals or tuple())


class MySQLConn (Conn):
    def __init__(self, db_profile='default'):
        config = ConfigParser.RawConfigParser()
        config.readfp(open(os.path.join(fanfoot.cur_dir, 'mysql.ini')))

        self._conn = mysql.connect(
            db=config.get(db_profile, 'db'),
            user=config.get(db_profile, 'user'),
            passwd=config.get(db_profile, 'password'))
        self._cursor = self._conn.cursor(mysql.cursors.DictCursor)

        if self.execute('SHOW TABLES').rowcount == 0:
            _new_mysql_db(self)

    def execute(self, sql, vals=None):
        # Wtf is wrong with people?
        sql = sql.replace('?', '%s')
        self._cursor.execute(sql, vals)
        return self._cursor

def _new_sqlite_db(conn):
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
            player_pos TEXT,
            PRIMARY KEY (league_key, season, team_id, week,
                         player_gsisid, player_team)
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
            team2_name TEXT,
            PRIMARY KEY (league_key, season, week, team1_id, team2_id)
        )
    ''')
    conn.execute('''
        CREATE TABLE status (
            kind TEXT,
            season TEXT,
            week INTEGER
        )
    ''')
    conn.execute('''
        CREATE TABLE score (
            league_key TEXT,
            season TEXT,
            week INTEGER,
            gsis_id TEXT,
            player_name TEXT,
            score REAL,
            PRIMARY KEY (league_key, season, week, gsis_id)
        )
    ''')
    conn.execute('''
        CREATE TABLE game (
            game_id TEXT,
            week INTEGER,
            home TEXT,
            away TEXT,
            score_home INTEGER,
            score_away INTEGER,
            time TEXT,
            PRIMARY KEY (game_id)
        )
    ''')
    conn.execute('''
        CREATE TABLE play (
            game_id TEXT,
            week INTEGER,
            play_id INTEGER,
            team TEXT,
            home INTEGER,
            descript TEXT,
            note TEXT,
            down INTEGER,
            yards_togo INTEGER,
            time TEXT,
            yardline TEXT,
            timeline INTEGER DEFAULT 0,
            PRIMARY KEY (game_id, play_id),
            UNIQUE (week, game_id, play_id)
        )
    ''')
    conn.execute('''
        CREATE INDEX ind_play_game_id ON play (game_id)
    ''')
    conn.execute('''
        CREATE TABLE play_stat (
            game_id TEXT,
            play_id INTEGER,
            stat TEXT,
            value INTEGER DEFAULT 0,
            PRIMARY KEY (game_id, play_id, stat)
        )
    ''')
    # conn.execute(''' 
        # CREATE INDEX ind_play_stat_game_id ON play_stat (game_id) 
    # ''') 
    conn.execute('''
        CREATE TABLE player_stat (
            game_id TEXT,
            week INTEGER,
            player_id TEXT,
            player_name TEXT,
            home INTEGER,
            stat TEXT,
            value INTEGER DEFAULT 0,
            PRIMARY KEY (game_id, player_id, stat),
            UNIQUE (week, player_id, stat)
        )
    ''')
    # conn.execute(''' 
        # CREATE INDEX ind_player_stat_game_id ON player_stat (game_id) 
    # ''') 
            
    conn.commit()
    return conn

def _new_mysql_db(conn):
    conn.execute('''
        CREATE TABLE roster (
            league_key VARCHAR (255),
            season VARCHAR (255),
            team_id TINYINT (255) UNSIGNED,
            team_name VARCHAR (255),
            week TINYINT (255) UNSIGNED,
            player_gsisid VARCHAR (255),
            player_name VARCHAR (255),
            player_team CHAR (3),
            player_pos VARCHAR (255),
            PRIMARY KEY (league_key, season, team_id, week,
                         player_gsisid, player_team)
        ) ENGINE=InnoDB
    ''')
    conn.execute('''
        CREATE TABLE matchup (
            league_key VARCHAR (255),
            season VARCHAR (255),
            week TINYINT (255) UNSIGNED,
            team1_id TINYINT (255) UNSIGNED,
            team1_name VARCHAR (255),
            team2_id TINYINT (255) UNSIGNED,
            team2_name VARCHAR (255),
            PRIMARY KEY (league_key, season, week, team1_id, team2_id)
        ) ENGINE=InnoDB
    ''')
    conn.execute('''
        CREATE TABLE status (
            kind VARCHAR (255),
            season VARCHAR (255),
            week TINYINT (255) UNSIGNED
        ) ENGINE=InnoDB
    ''')
    conn.execute('''
        CREATE TABLE score (
            league_key VARCHAR (50),
            season VARCHAR (10),
            week TINYINT UNSIGNED,
            gsis_id VARCHAR (100),
            player_name VARCHAR (255),
            score FLOAT (24),
            PRIMARY KEY (league_key, season, week, gsis_id)
        ) ENGINE=InnoDB
    ''')
    conn.execute('''
        CREATE TABLE game (
            game_id VARCHAR (255),
            week TINYINT (255) UNSIGNED,
            home VARCHAR (255),
            away VARCHAR (255),
            score_home TINYINT (255) UNSIGNED,
            score_away TINYINT (255) UNSIGNED,
            time VARCHAR (255),
            PRIMARY KEY (game_id)
        ) ENGINE=InnoDB
    ''')
    conn.execute('''
        CREATE TABLE play (
            game_id VARCHAR (255),
            week TINYINT (255) UNSIGNED,
            play_id SMALLINT UNSIGNED,
            team VARCHAR (255),
            home TINYINT (255) UNSIGNED,
            descript TEXT,
            note VARCHAR (255),
            down TINYINT (255) UNSIGNED,
            yards_togo TINYINT (255) UNSIGNED,
            time VARCHAR (255),
            yardline VARCHAR (255),
            timeline INT DEFAULT 0,
            PRIMARY KEY (game_id, play_id),
            UNIQUE (week, game_id, play_id)
        ) ENGINE=InnoDB
    ''')
    conn.execute('''
        CREATE INDEX ind_play_game_id ON play (game_id)
    ''')
    conn.execute('''
        CREATE TABLE play_stat (
            game_id VARCHAR (255),
            play_id SMALLINT UNSIGNED,
            stat VARCHAR (255),
            value SMALLINT DEFAULT 0,
            PRIMARY KEY (game_id, play_id, stat)
        ) ENGINE=InnoDB
    ''')
    # conn.execute(''' 
        # CREATE INDEX ind_play_stat_game_id ON play_stat (game_id) 
    # ''') 
    conn.execute('''
        CREATE TABLE player_stat (
            game_id VARCHAR (255),
            week TINYINT (255) UNSIGNED,
            player_id VARCHAR (255),
            player_name VARCHAR (255),
            home TINYINT (1) UNSIGNED,
            stat VARCHAR (255),
            value SMALLINT DEFAULT 0,
            PRIMARY KEY (game_id, player_id, stat),
            UNIQUE (week, player_id, stat)
        ) ENGINE=InnoDB
    ''')
    # conn.execute(''' 
        # CREATE INDEX ind_player_stat_game_id ON player_stat (game_id) 
    # ''') 
            
    conn.commit()
    return conn


