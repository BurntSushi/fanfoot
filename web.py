import urllib

import bottle

import nflgame.live
import nflgame.schedule

import fanfoot
import fanfoot.player

app = bottle.Bottle()

@app.route('/static/<filepath:path>')
def static(filepath):
    return bottle.static_file(filepath, root='./web/static/')


@app.route('/', name='home')
@bottle.view('home')
def home():
    leagues = fanfoot.leagues().values()
    return dict(title='Home', leagues=leagues)


@app.route('/plays/<league_teams>', name='plays')
@app.route('/plays/<league_teams>/<week:int>', name='plays_week')
@bottle.view('plays')
def plays(league_teams, week=None):
    db = fanfoot.conn()
    bench = bottle.request.query.bench == '1'
    live = bottle.request.query.live == '1'
    if week is None:
        week = db.get_week()

    teams = find_teams_players(db, week, league_teams, bench=bench)
    games = db.games(week)
    plays = db.plays(week)

    def play_sort_notime(p):
        ginfo = nflgame.schedule.games_byid[p.game_id]
        return (nflgame.live._game_datetime(ginfo), p.play_id)
    def play_sort_live(p):
        return (p.timeline, p.play_id)
    plays = sorted(plays, reverse=True,
                   key=play_sort_live if live else play_sort_notime)

    all_players = set()
    for _, players in teams:
        for group in players:
            for player in group:
                if player.stats is None:
                    continue
                all_players.add(player.stats.player_name)

    def highlight_play(play):
        for player_name in all_players:
            if player_name in play.desc:
                return True
        return False

    def week_url(week):
        query_pairs = {'bench': int(bench), 'live': int(live)}
        return url_query('plays_week', query_pairs,
                         league_teams=league_teams, week=week)

    return dict(
        nflgame_schedule=nflgame.schedule,
        db=db,
        week=week,
        games=games,
        plays=plays,
        teams=teams,
        highlight_play=highlight_play,
        bench=bench,
        live=live,
        week_url=week_url,
        bench_url=url_query('plays_week',
                            {'bench': 0 if bench else 1,
                             'live': int(live)},
                            league_teams=league_teams, week=week),
        live_url=url_query('plays_week',
                           {'bench': int(bench),
                            'live': 0 if live else 1},
                            league_teams=league_teams, week=week),
    )

@app.route('/league/<labels>', name='league')
@app.route('/league/<labels>/<week:int>', name='league_week')
@bottle.view('league')
def league(labels, week=None):
    db = fanfoot.conn()
    if week is None:
        week = db.get_week()

    leagues = []
    for label in labels.split(','):
        leagues.append(find_league(label))

    def week_url(week):
        return url_query('league_week', {}, labels=labels, week=week)

    return dict(
        db=db,
        leagues=leagues,
        week=week,
        week_url=week_url,
    )


@app.route('/team-details', method='POST')
def team_details():
    league_teams = []
    for league_team in sorted(bottle.request.forms.getall('teams')):
        league_teams.append(league_team)
    bottle.redirect(app.get_url('team_week',
                                league_teams=','.join(league_teams),
                                week=bottle.request.forms.get('week')))


@app.route('/team/<league_teams>', name='team')
@app.route('/team/<league_teams>/<week:int>', name='team_week')
@bottle.view('team')
def team(league_teams, week=None):
    db = fanfoot.conn()
    bench = bottle.request.query.bench == '1'
    detailed = bottle.request.query.detailed == '1'
    headers = fanfoot.player.highlight_headers()
    if week is None:
        week = db.get_week()

    teams = find_teams_players(db, week, league_teams, bench=bench)
    tables = []
    for team, players in teams:
        total = 0.0
        table = []
        for i, (group, header) in enumerate(zip(players, headers)):
            if detailed:
                table.append(header + ['Score'])
            else:
                table.append(header[0:3] + ['Score'])

            for player in group:
                row = player.highlights(get_stats=True)
                score = None

                s = player.computed_score
                if s is not None:
                    score = '%0.2f' % s
                    if player.pos != 'BN':
                        total += s
                else:
                    score = '-'
                if detailed:
                    row += [score]
                else:
                    row = row[0:3] + [score]

                if player.playing():
                    row = ['*'] + row

                table.append(row)
            table.append('')


        max_row = max([len(row) for row in table
                                if len(row) > 0 and row[0] != '*'])
        total_row = [''] * max_row
        total_row[-2] = 'TOTAL:'
        if total == 0.0:
            total_row[-1] = '-'
        else:
            total_row[-1] = '%0.2f' % total
        table.append(total_row)

        tables.append((team, max_row, table))

    def week_url(week):
        query_pairs = {'bench': int(bench), 'detailed': int(detailed)}
        return url_query('team_week', query_pairs,
                         league_teams=league_teams, week=week)

    return dict(
        db=db,
        teams=teams,
        week=week,
        week_url=week_url,
        tables=tables,
        bench=bench,
        detailed=detailed,
        bench_url=url_query('team_week',
                            {'bench': 0 if bench else 1,
                             'detailed': int(detailed)},
                            league_teams=league_teams, week=week),
        detailed_url=url_query('team_week',
                               {'bench': int(bench),
                                'detailed': 0 if detailed else 1},
                               league_teams=league_teams, week=week),
    )


def find_teams_players(db, week, league_teams, bench=False):
    teams = []
    for league_team in league_teams.split(','):
        label, team_or_id = league_team.split(':')

        league = find_league(label)
        team = find_team(db, league, team_or_id)
        players = db.roster(league, week, team.id, bench=bench) or []

        teams.append((team, fanfoot.player.group(players)))
    return teams

def find_league(label):
    for league in fanfoot.leagues().itervalues():
        if league.label == label:
            return league
    bottle.abort(404, 'Could not find league "%s".' % label)

def find_team(db, league, team_or_id):
    team = db.find_team(league, team_or_id)
    if not team:
        bottle.abort(404, 'Could not find team %s in league %s.'
                          % (team_or_id, league.label))
    if len(team) > 1:
        bottle.abort(404, 'Too many matches for team %s in league %s.'
                          % (team_or_id, league.label))
    return team[0]

def url(name, route_name, **kwargs):
    return '<a href="%s">%s</a>' % (app.get_url(route_name, **kwargs), name)

def url_query(route_name, pairs, **kwargs):
    base_url = app.get_url(route_name, **kwargs)
    if not pairs:
        return base_url
    query = urllib.urlencode([(k, v) for k, v in pairs.iteritems()])
    return '%s?%s' % (base_url, query)


bottle.TEMPLATE_PATH.append('./web/')
bottle.SimpleTemplate.defaults['url'] = url
bottle.SimpleTemplate.defaults['url_query'] = url_query

# bottle.SimpleTemplate.defaults['norefresh'] = True 

bottle.run(app=app, host='0.0.0.0', port=8090, reloader=True)

