%rebase layout title=get('title', '???')

<ul>
  %all_leagues = []
  %for league in sorted(leagues, key=lambda lg: lg.label):
    %all_leagues.append(league.label)
    <li>{{!url(league.label, 'league', labels=league.label)}}</li>
  %end
  <li>{{!url("All leagues", 'league', labels=','.join(all_leagues))}}</li>
</ul>

