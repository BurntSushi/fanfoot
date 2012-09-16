from collections import namedtuple

import fantasy

_MAX_GAME_SCORE = 999.0

# These settings reflect standard scoring at Yahoo.
_default = [
    ('round', 2.0),
    ('passing_yds', 0.04), ('passing_tds', 4.0), ('passing_int', -1.0),
    ('rushing_yds', 0.1), ('rushing_tds', 6.0),
    ('receiving_yds', 0.1), ('receiving_tds', 6.0), ('receiving_rec', 0.0),
    ('kickret_tds', 6.0), ('puntret_tds', 6.0),
    ('twoptm', 2.0),
    ('fumbles_lost', -2.0), ('fumbles_rec_tds', 6.0),

    ('xp', 1.0), ('xp_missed', 0.0),
    ('fg0_19', 3.0), ('fg20_29', 3.0), ('fg30_39', 3.0),
    ('fg40_49', 4.0), ('fg50', 5.0),
    ('fg0_19_missed', 0.0), ('fg20_29_missed', 0.0), ('fg30_39_missed', 0.0),
    ('fg40_49_missed', 0.0), ('fg50_missed', 0.0),

    ('defense_sk', 1.0), ('defense_int', 2.0), ('defense_frec', 2.0),
    ('defense_tds', 6.0), ('defense_safe', 2.0),
    ('defense_fgblk', 2.0), ('defense_puntblk', 2.0), ('defense_xpblk', 2.0),
    ('defense_krtds', 6.0), ('defense_prtds', 6.0),
    ('defense_pa_cat', [0.0, 6.0, 13.0, 20.0, 27.0, 34.0, _MAX_GAME_SCORE]),
    ('defense_pa_pts', [10.0, 7.0, 4.0, 1.0, 0.0, -1.0, -4.0]),
]

Config = namedtuple('Config', [f[0] for f in _default])

default_conf = Config(**dict(_default))

def score(player):
    if isinstance(player, fantasy.player.OffensePlayer):
        return _score_offense(player)
    elif isinstance(player, fantasy.player.KickingPlayer):
        return _score_kicking(player)
    elif isinstance(player, fantasy.player.DefensePlayer):
        return _score_defense(player)

    assert False, 'I do not know how to score %s players.' % type(player)

def _score_offense(player):
    conf = player.lgconf.scoring
    stats = player.game_stats()
    if stats is None:
        return None

    s = 0.0

    s += conf.passing_yds * stats.passing_yds
    s += conf.passing_tds * stats.passing_tds
    s += conf.passing_int * stats.passing_int

    s += conf.rushing_yds * stats.rushing_yds
    s += conf.rushing_tds * stats.rushing_tds

    s += conf.receiving_yds * stats.receiving_yds
    s += conf.receiving_rec * stats.receiving_rec
    s += conf.receiving_tds * stats.receiving_tds

    s += conf.kickret_tds * stats.kickret_tds
    s += conf.puntret_tds * stats.puntret_tds
    s += conf.fumbles_rec_tds * stats.fumbles_rec_tds

    s += conf.twoptm * stats.twoptm
    s += conf.fumbles_lost * stats.fumbles_lost

    return round(s, int(conf.round))

def _score_kicking(player):
    def fgmissed((fg_made, fg_att)):
        return fg_att - fg_made

    conf = player.lgconf.scoring
    stats = player.game_stats()
    if stats is None:
        return None

    fgs = player.field_goals()
    fg0, fg20, fg30, fg40, fg50 = fantasy.player.group_field_goals(fgs)

    s = 0.0

    s += conf.xp * stats.kicking_xpmade
    s += conf.xp_missed * stats.kicking_xpmissed

    s += conf.fg0_19 * fg0[0]
    s += conf.fg20_29 * fg20[0]
    s += conf.fg30_39 * fg30[0]
    s += conf.fg40_49 * fg40[0]
    s += conf.fg50 * fg50[0]

    s += conf.fg0_19_missed * fgmissed(fg0)
    s += conf.fg20_29_missed * fgmissed(fg20)
    s += conf.fg30_39_missed * fgmissed(fg30)
    s += conf.fg40_49_missed * fgmissed(fg40)
    s += conf.fg50_missed * fgmissed(fg50)

    return round(s, int(conf.round))

def _score_defense(defense):
    conf = defense.lgconf.scoring
    if len(list(defense.players())) == 0:
        return None

    s = 0.0

    s += conf.defense_sk * defense.sacks
    s += conf.defense_int * defense.ints
    s += conf.defense_frec * defense.fumrecs
    s += conf.defense_tds * defense.tds
    s += conf.defense_safe * defense.safeties
    s += conf.defense_fgblk * defense.fgblks
    s += conf.defense_puntblk * defense.puntblks
    s += conf.defense_xpblk * defense.xpblks
    s += conf.defense_krtds * defense.krtds
    s += conf.defense_prtds * defense.prtds

    pts_allowed = defense.points_allowed 
    for pa, pts in zip(conf.defense_pa_cat, conf.defense_pa_pts):
        if pts_allowed <= pa:
            s += pts
            break

    return round(s, int(conf.round))

def create_config(d):
    """
    Takes an arbitrary dictionary and returns a new instance of Config where
    the default scoring values are overwritten by any corresponding fields
    in the dict d. If a particular field is not in d, then the default value
    will be used.

    All values are converted to floats or lists of floats.

    A key in d that is not a valid scoring field will be ignored.
    """
    dconf = dict(_default)
    for k, v in d.iteritems():
        if k not in dconf:
            continue
        
        # Handle the special fields that are lists first.
        if k == 'defense_pa_cat':
            vals = v.split()
            if vals.index('+') != -1:
                vals[vals.index('+')] = _MAX_GAME_SCORE
            dconf['defense_pa_cat'] = map(float, vals)
        elif k == 'defense_pa_pts':
            dconf['defense_pa_pts'] = map(float, v.split())
        else:
            dconf[k] = float(v)

    assert len(dconf['defense_pa_cat']) == len(dconf['defense_pa_pts'])

    return Config(**dconf)
