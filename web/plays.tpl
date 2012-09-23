%rebase layout title='Plays for week %s' % week

%include weeks cur_week=week, week_url=week_url

<ul class="options">
  <li>
    <a href="{{bench_url}}">{{"No bench" if bench else "Show bench"}}</a>
  </li>
  <li>
    <a href="{{live_url}}">{{"Sort by start" if live else "Sort live"}}</a>
  </li>
  <li>
    <a href="{{short_url}}">{{"Long" if short else "Short"}}</a>
  </li>
</ul>

<h2>Plays for week {{week}}</h2>
<table>
  <tr>
    %if not short:
      <th>Start</th>
      <th>Time</th>
      <th>Home</th>
      <th>Away</th>
      <th>Down</th>
      <th>Yd Line</th>
    %else:
      <th>Home</th>
      <th>Away</th>
    %end
    <th>Play</th>
  </tr>

  %for p in plays:
    %g = games[p.game_id]
    %sched = nflgame_schedule.games_byid[p.game_id]
    %if highlight_play(p):
      <tr class="highlighted">
    %else:
      <tr>
    %end

    %h_poss = ' poss' if p.team == g.home else ''
    %a_poss = ' poss' if p.team == g.away else ''

      %if not short:
        <td class="nowrap">{{sched['wday']}}, {{sched['time']}}</td>
        <td class="nowrap">{{p.time}}</td>
        <td class="nowrap{{h_poss}}">{{g.home}} ({{g.score_home}})</td>
        <td class="nowrap{{a_poss}}">{{g.away}} ({{g.score_away}})</td>
        <td class="nowrap">{{p.down}} and {{p.yards_togo}}</td>
        <td class="nowrap">{{p.yardline}}</td>
      %else:
        <td class="nowrap{{h_poss}}">{{g.home}} ({{g.score_home}})</td>
        <td class="nowrap{{a_poss}}">{{g.away}} ({{g.score_away}})</td>
      %end
      <td>{{p.desc}}</td>
    </tr>
  %end
</table>
