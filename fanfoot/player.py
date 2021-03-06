import nflgame.player
import nflgame.seq

import fanfoot
import fanfoot.stats

_HEADERS = {
    'offense': [('pos', 'Pos'), ('team', 'Team'), ('name', 'Name'),
                ('passing_cmp', 'Ps Cmp'),
                ('passing_yds', 'Ps Yds'),
                ('passing_tds', 'Ps TDs'),
                ('passing_int', 'Ps Int'),
                ('rushing_att', 'Rh Att'),
                ('rushing_yds', 'Rh Yds'),
                ('rushing_tds', 'Rh TDs'),
                ('receiving_rec', 'Rc Rec'),
                ('receiving_yds', 'Rc Yds'),
                ('receiving_tds', 'Rc TDs'),
                ('twoptm', '2-ptc'),
                ('fumlost', 'F.Lst'),
               ],
    'kicking': [('pos', 'Pos'), ('team', 'Team'), ('name', 'Name'),
                ('', ''), ('', ''), ('', ''), ('', ''), ('', ''), ('', ''),
                ('xp', 'XP'),
                ('fg0_19', 'FG 0-19'),
                ('fg20_29', 'FG 20-29'),
                ('fg30_39', 'FG 30-39'),
                ('fg40_49', 'FG 40-49'),
                ('fg50', 'FG 50+'),
               ],
    'defense': [('pos', 'Pos'), ('team', 'Team'), ('name', 'Name'),
                ('', ''),
                ('', ''),
                ('', ''),
                ('tds', 'TDs'),
                ('int', 'INT'),
                ('fumrec', 'Fum Rec'),
                ('sack', 'Sack'),
                ('safety', 'Safe'),
                ('pa', 'PA'),
                ('ktd', 'KTD'),
                ('prtd', 'PRTD'),
                ('blk', 'BLK'),
               ],
}

def group(players):
    """
    Returns a triple of offensive, kicker and defense players.
    """
    offense, kickers, defense = [], [], []
    for p in players:
        if p.player.position == 'K':
            kickers.append(p)
        elif p.player.position == 'DEF':
            defense.append(p)
        elif p.player.position == 'IR':
            continue  # Ignore injured reserve players for now.
        else:
            offense.append(p)
    return (offense, kickers, defense)

def group_field_goals(fgs):
    """
    Returns five-tuple of the number of fields goals made and field goals
    attempt for each of the following field goal lengths: 0-19 yards,
    20-29 yards, 30-39 yards, 40-49 yards and 50+ yards.

    fgs should be a list of tuples where the first value is the number of
    yards of the field goal attempt and the second value is whether
    the attempt was good.
    """
    fgs0_19m, fgs20_29m, fgs30_39m, fgs40_49m, fgs50m = 0, 0, 0, 0, 0
    fgs0_19a, fgs20_29a, fgs30_39a, fgs40_49a, fgs50a = 0, 0, 0, 0, 0
    for yards, good in fgs:
        if yards <= 19:
            fgs0_19a += 1
            if good:
                fgs0_19m += 1
        elif yards <= 29:
            fgs20_29a += 1
            if good:
                fgs20_29m += 1
        elif yards <= 39:
            fgs30_39a += 1
            if good:
                fgs30_39m += 1
        elif yards <= 49:
            fgs40_49a += 1
            if good:
                fgs40_49m += 1
        else:
            fgs50a += 1
            if good:
                fgs50m += 1

    return ((fgs0_19m, fgs0_19a),
            (fgs20_29m, fgs20_29a),
            (fgs30_39m, fgs30_39a),
            (fgs40_49m, fgs40_49a),
            (fgs50m, fgs50a))

def highlight_headers():
    """
    Returns a triple of offensive, kicking and defense headers. All three
    lists are guaranteed to be the same length.
    """
    offense =  [h[1] for h in _HEADERS['offense']]
    kicking = [h[1] for h in _HEADERS['kicking']]
    defense = [h[1] for h in _HEADERS['defense']]
    return (offense, kicking, defense)


def _create_statrow(cat, d):
    """
    Takes a dict d keyed by statistical fields in _HEADERS with values
    corresponding to the actual stats in the statistical category named
    by cat.

    A list is returned of the appropriate length with each cell filled
    with the correct value according to _HEADERS.
    """
    lst = []
    for field, _ in _HEADERS[cat]:
        lst.append(d.get(field, '-'))
    return lst

def create_player(db, lgconf, week, gsis_id, pos, team, name):
    if name == team:  # Defense!
        playermeta = nflgame.player.PlayerDefense(team)
    else:
        playermeta = nflgame.players[gsis_id]

    if playermeta.position == 'K':
        init = KickingPlayer
    elif playermeta.position == 'DEF':
        init = DefensePlayer
    else:
        init = OffensePlayer

    return init(db, lgconf, week, gsis_id, pos, team, name, playermeta)

class Player (object):
    def __init__(self, db, lgconf, week, gsis_id, pos, team, name, playermeta): 
        self.db = db
        self.lgconf = lgconf
        self.week = week
        self.pos = pos
        self.team = team
        self.name = name
        self.player = playermeta
        self.playerid = gsis_id
        self.computed_score = fanfoot.stats.score(self.db, lgconf,
                                                  week, gsis_id)

        self._base_info = {
            'pos': self.pos,
            'team': self.team,
            'name': self.name,
        }

        self._game = fanfoot.stats.game(self.db, 2012, self.week, self.team)
        if self._game is None:
            self.stats = None
        else:
            self.stats = fanfoot.stats.player(self.db, self._game.game_id,
                                              self.playerid)

    def _add_base_info(self, d):
        newd = {}
        for k, v in self._base_info.iteritems():
            newd[k] = v
        for k, v in d.iteritems():
            newd[k] = v
        return newd

    def score(self):
        return fanfoot.scoring.score(self)

    def plays(self):
        return fanfoot.stats.plays(self.db, self._game.game_id)

    def game(self):
        return self._game

    def game_stats(self):
        return self.stats

    def playing(self):
        if self._game is None:
            return None
        return self._game.playing

    def highlights(self, get_stats=True):
        assert False, 'subclass responsibility'

    def __str__(self):
        return '%s (%s, %s)' % (self.name, self.team, self.pos)

class OffensePlayer (Player):
    def highlights(self, get_stats=True):
        base = _create_statrow('offense', self._base_info)
        if not get_stats:
            return base

        stats = self.game_stats()
        if stats is None:
            return base

        return _create_statrow('offense', self._add_base_info({
            'passing_cmp': '%d/%d' % (stats.passing_cmp, stats.passing_att),
            'passing_yds': int(stats.passing_yds),
            'passing_tds': int(stats.passing_tds),
            'passing_int': int(stats.passing_int),
            'rushing_att': int(stats.rushing_att),
            'rushing_yds': int(stats.rushing_yds),
            'rushing_tds': int(stats.rushing_tds),
            'receiving_rec': '%d/%d' % (stats.receiving_rec,
                                        stats.receiving_tar),
            'receiving_yds': int(stats.receiving_yds),
            'receiving_tds': int(stats.receiving_tds),
            'twoptm': int(stats.twoptm),
            'fumlost': int(stats.fumbles_lost),
        }))

class KickingPlayer (Player):
    def field_goals(self):
        g = self.game()
        if g is None:
            return []

        fgs = []
        for play in self.plays():
            if play.kicking_fga == 0:
                continue

            # XXX: This will fail if there is more than FG kicker in a game.
            stats = fanfoot.stats.player(self.db, self._game.game_id,
                                         self.playerid)
            if stats is None or stats.home != play.home:
                continue

            if play.kicking_fgm > 0:
                fgs.append((play.kicking_fgm_yds, True))
            else:
                fgs.append((play.kicking_fgmissed_yds, False))
        return fgs

    def highlights(self, get_stats=True):
        base = _create_statrow('kicking', self._base_info)
        if not get_stats:
            return base

        stats = self.game_stats()
        fgs = self.field_goals()
        if not fgs:
            return base

        fg0, fg20, fg30, fg40, fg50 = group_field_goals(fgs)
        return _create_statrow('kicking', self._add_base_info({
            'xp': '%d/%d' % (stats.kicking_xpmade, stats.kicking_xpa),
            'fg0_19': '%d/%d' % (fg0[0], fg0[1]),
            'fg20_29': '%d/%d' % (fg20[0], fg20[1]),
            'fg30_39': '%d/%d' % (fg30[0], fg30[1]),
            'fg40_49': '%d/%d' % (fg40[0], fg40[1]),
            'fg50': '%d/%d' % (fg50[0], fg50[1]),
        }))

class DefensePlayer (Player):
    def highlights(self, get_stats=True):
        base = _create_statrow('defense', self._base_info)
        if not get_stats:
            return base

        if len(list(self.players())) == 0:
            return base

        return _create_statrow('defense', self._add_base_info({
            'tds': int(self.tds),
            'int': int(self.ints),
            'fumrec': int(self.fumrecs),
            'sack': self.sacks,
            'safety': int(self.safeties),
            'pa': int(self.points_allowed),
            'ktd': int(self.krtds),
            'prtd': int(self.prtds),
            'blk': int(self.blocks),
        }))

    @property
    def tds(self):
        return self._count_stat('defense_tds')

    @property
    def ints(self):
        return self._count_stat('defense_int')

    @property
    def fumrecs(self):
        return self._count_stat('defense_frec')

    @property
    def sacks(self):
        cnt = 0.0
        for p in self.players().filter(defense_sk__ge=0.5):
            cnt += p.defense_sk
        return cnt

    @property
    def safeties(self):
        return self._count_stat('defense_safe')

    @property
    def blocks(self):
        return self.xpblks + self.fgblks + self.puntblks

    @property
    def xpblks(self):
        return self._count_stat('defense_xpblk')

    @property
    def fgblks(self):
        return self._count_stat('defense_fgblk')

    @property
    def puntblks(self):
        return self._count_stat('defense_puntblk')

    @property
    def krtds(self):
        return self._count_stat('kickret_tds')

    @property
    def prtds(self):
        return self._count_stat('puntret_tds')

    @property
    def points_allowed(self):
        game = self.game()
        if game is None:
            return 0

        home = game.home == self.name
        if self.lgconf.kind == 'espn':
            if game.home == self.name:
                return game.score_away
            else:
                return game.score_home
        elif self.lgconf.kind == 'yahoo':
            # This is weird. Yahoo only counts certain points in the
            # "points allowed" category. Since most points are against the
            # defense, we compute this in the negative: start with the total
            # points allowed, and subtract the following forms of scoring:
            # interception return tds, fumble return tds, blocked field
            # goal return tds and safeties. We do the subtraction iteratively
            # over each play in the game.
            pa = game.score_away if home else game.score_home
            for play in self.plays():
                # We're only subtracting points when the defense isn't
                # on the field.
                if home != play.home:
                    continue

                if play.defense_safe > 0:
                    pa -= 2
                elif play.defense_int_tds > 0:
                    pa -= 6
                elif play.defense_frec_tds > 0:
                    pa -= 6
                elif play.defense_misc_tds > 0:
                    # This can refer to either field goal returns for td
                    # or punt blocks for tds. Curiously, only the punt block
                    # returns are counted as points allowed. So if the play
                    # description contains the phrase 'field goal', subtract
                    # the td from the points allowed.
                    if 'field goal' in play.desc.lower():
                        pa -= 6
            return pa

        assert False, 'I don\'t know how to compute PA for %s leagues.' \
                      % self.lgconf.kind

    def players(self):
        game = self.game()
        if game is None:
            return nflgame.seq.GenPlayerStats([])

        home = game.home == self.name
        player_gen = fanfoot.stats.players(self.db, self._game.game_id)
        return nflgame.seq.GenPlayerStats(player_gen).filter(home=home)

    def _count_stat(self, stat):
        cnt = 0
        for p in self.players().filter(**{'%s__ge' % stat: 1}):
            cnt += getattr(p, stat)
        return cnt

    def game_stats(self):
        assert False, 'invalid'

