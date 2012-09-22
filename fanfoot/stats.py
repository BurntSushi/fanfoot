_cache_games = {}
_cache_weeks = set()
_cache_plays = {}
_cache_all_plays = {}
_cache_players = {}
_cache_scores = {}

def clear():
    global _cache_games, _cache_weeks, _cache_plays, \
           _cache_all_plays, _cache_players, _cache_scores
    _cache_games = {}
    _cache_weeks = set()
    _cache_plays = {}
    _cache_all_plays = {}
    _cache_players = {}
    _cache_scores = {}

def score(db, lgconf, week, gsis_id):
    if week not in _cache_scores or lgconf.key not in _cache_scores[week]:
        _load_scores(db, lgconf, week)
    return _cache_scores[week][lgconf.key].get(gsis_id, 0.0)

def player(db, game_id, gsis_id):
    g = game_by_id(db, game_id)
    if g.week not in _cache_players:
        _load_players(db, g.week)
    return _cache_players[g.week].get(gsis_id, None)

def players(db, game_id):
    g = game_by_id(db, game_id)
    if g.week not in _cache_players:
        _load_players(db, g.week)
    for p in _cache_players[g.week].itervalues():
        if p.game_id == game_id:
            yield p

def plays(db, game_id):
    g = game_by_id(db, game_id)
    if g.week not in _cache_plays:
        _load_plays(db, g.week)
    for play in _cache_plays[g.week]:
        if play.game_id == game_id:
            yield play

def all_plays(db, game_id):
    g = game_by_id(db, game_id)
    if g.week not in _cache_all_plays:
        _cache_all_plays[g.week] = {}
        for p in db.plays(g.week):
            _cache_all_plays[g.week][(game_id, p.play_id)] = p
    return _cache_all_plays[g.week]

def game(db, year, week, team):
    if week not in _cache_weeks:
        _load_games(db, week)
    for game_id, g in _cache_games.iteritems():
        if g.week == week and team in (g.home, g.away):
            return g
    return None

def game_by_id(db, game_id):
    if game_id not in _cache_games.iteritems():
        g = db.game_by_id(game_id)
        _load_games(db, g.week)
    return _cache_games[game_id]

def _load_games(db, week):
    for k, v in db.games(week).iteritems():
        _cache_games[k] = v
    _cache_weeks.add(week)

def _load_plays(db, week):
    _cache_plays[week] = db.plays(week)

def _load_players(db, week):
    _cache_players[week] = db.players(week)

def _load_scores(db, lgconf, week):
    if week not in _cache_scores:
        _cache_scores[week] = {}
    _cache_scores[week][lgconf.key] = db.scores(lgconf, week)

