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
    Returns a triple of offensive, kicker and defense headers. All three
    lists are guaranteed to be the same length.
    """
    offense =  ['Pos', 'Team', 'Name',
                'Pass Cmp', 'Pass Yds', 'Pass TDs',
                'Rush Att', 'Rush Yds', 'Rush TDs',
                'Recv Rec', 'Recv Yds', 'Recv TDs',
               ]
    kickers = ['Pos', 'Team', 'Name',
               '', '', '',
               'XP', 'FG 0-19', 'FG 20-29', 'FG 30-39', 'FG 40-49', 'FG 50+',
              ]
    defense = ['Pos', 'Team', 'Name',
               '', '', '', '', '', '', '', '', '',
              ]
    return (offense, kickers, defense)

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

    def game(self):
        # return nflgame.one( 
            # year=2011, 
            # week=14, 
            # home=self.team, 
            # away=self.team) 
        return nflgame.one(
            year=int(self.lgconf.season),
            week=self.week,
            home=self.team,
            away=self.team)

    def game_stats(self):
        g = self.game()
        if g is None:
            return None
        return g.drives.players().playerid(self.player.playerid)

    def field_goals(self):
        g = self.game()
        if g is None:
            return None
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

    def highlights(self):
        if self.player.position == 'K':
            return self.__kicker_highlights()
        elif self.player.position == 'DEF':
            return self.__defense_highlights()
        return self.__offense_highlights()

    def __offense_highlights(self):
        stats = self.game_stats()
        if stats is None:
            return []
        return [
            stats.passing_cmp,
            stats.passing_yds,
            stats.passing_tds,
            stats.rushing_att,
            stats.rushing_yds,
            stats.rushing_tds,
            stats.receiving_rec,
            stats.receiving_yds,
            stats.receiving_tds,
        ]

    def __kicker_highlights(self):
        stats = self.game_stats()
        fg0, fg20, fg30, fg40, fg50 = group_field_goals(self.field_goals())
        return [
            '', '', '',
            '%d/%d' % (stats.kicking_xpmade, stats.kicking_xpa),
            '%d/%d' % (fg0[0], fg0[1]),
            '%d/%d' % (fg20[0], fg20[1]),
            '%d/%d' % (fg30[0], fg30[1]),
            '%d/%d' % (fg40[0], fg40[1]),
            '%d/%d' % (fg50[0], fg50[1]),
        ]

    def __defense_highlights(self):
        return []

