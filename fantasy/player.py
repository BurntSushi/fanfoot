import nflgame
import nflgame.player

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

_HEADERS = {
    'offense': [('pos', 'Pos'), ('team', 'Team'), ('name', 'Name'),
                ('passing_cmp', 'Pass Cmp'),
                ('passing_yds', 'Pass Yds'),
                ('passing_tds', 'Pass TDs'),
                ('passing_int', 'Pass Int'),
                ('rushing_att', 'Rush Att'),
                ('rushing_yds', 'Rush Yds'),
                ('rushing_tds', 'Rush TDs'),
                ('receiving_rec', 'Recv Rec'),
                ('receiving_yds', 'Recv Yds'),
                ('receiving_tds', 'Recv TDs'),
                ('twoptm', '2-pt Conv'),
                ('fumlost', 'Fum Lost'),
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
                ('', ''),
                ('', ''),
                ('', ''),
                ('', ''),
                ('', ''),
                ('', ''),
                ('', ''),
                ('', ''),
                ('', ''),
               ],
}

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
        lst.append(d.get(field, 0))
    return lst

class Player (object):
    def __init__(self, lgconf, week, gsis_id, pos, team, name): 
        if name == team:  # Defense!
            self.player = nflgame.player.PlayerDefense(team)
        else:
            self.player = nflgame.players[gsis_id]
        self.lgconf = lgconf
        self.week = week
        self.pos = pos
        self.team = team
        self.name = name

        self._base_info = {
            'pos': self.pos,
            'team': self.team,
            'name': self.name,
        }

    def _add_base_info(self, d):
        newd = {}
        for k, v in self._base_info.iteritems():
            newd[k] = v
        for k, v in d.iteritems():
            newd[k] = v
        return newd

    def game(self):
        return nflgame.one(
            year=int(self.lgconf.season),
            week=self.week,
            home=self.team,
            away=self.team)

    def game_stats(self):
        g = self.game()
        if g is None:
            return None
        return g.max_player_stats().playerid(self.player.playerid)

    def field_goals(self):
        g = self.game()
        if g is None:
            return []
        plays = g.drives.plays().filter(kicking_fga__gt=0)
        fgs = []
        for play in plays:
            stats = play.players.playerid(self.player.playerid)
            if stats is None:  # more than one FG kicker in a game?
                continue
            if stats.kicking_fgm > 0:
                fgs.append((stats.kicking_fgm_yds, True))
            else:
                fgs.append((stats.kicking_fgmissed_yds, False))
        return fgs

    def highlights(self, get_stats=True):
        if self.player.position == 'K':
            return self.__kicking_highlights(get_stats)
        elif self.player.position == 'DEF':
            return self.__defense_highlights(get_stats)
        return self.__offense_highlights(get_stats)

    def __offense_highlights(self, get_stats=True):
        base = _create_statrow('offense', self._base_info)
        if not get_stats:
            return base

        stats = self.game_stats()
        if stats is None:
            return base

        return _create_statrow('offense', self._add_base_info({
            'passing_cmp': stats.passing_cmp,
            'passing_yds': stats.passing_yds,
            'passing_tds': stats.passing_tds,
            'passing_int': stats.passing_int,
            'rushing_att': stats.rushing_att,
            'rushing_yds': stats.rushing_yds,
            'rushing_tds': stats.rushing_tds,
            'receiving_rec': stats.receiving_rec,
            'receiving_yds': stats.receiving_yds,
            'receiving_tds': stats.receiving_tds,
            'twoptm': stats.twoptm,
            'fum_lost': stats.fumbles_lost,
        }))

    def __kicking_highlights(self, get_stats=True):
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

    def __defense_highlights(self, get_stats=True):
        return _create_statrow('defense', self._base_info)

