%rebase layout norefresh=True, title='Scoreboard'

%include weeks cur_week=week, week_url=week_url

<form method="post" action="/team-details">
<input type="hidden" name="week" value="{{week}}" />
<div><input type="submit" value="Submit" /></div>

%for league in leagues:
  <div class="table">
    <h2>{{league.label}}</h2>
    <table>
    %for i, matchup in enumerate(db.matchups(league, week)):
      %if i > 0:
        <tr><td colspan="3">&nbsp;</td></tr>
      %end

      %t1, t2 = matchup.team1, matchup.team2

      %t1id = '%s:%s' % (t1.lgconf.label, t1.id)
      %t2id = '%s:%s' % (t2.lgconf.label, t2.id)

      %s1 = db.score_team(t1, week)
      %s2 = db.score_team(t2, week)
      <tr>
        <td><input type="checkbox" name="teams" id="{{t1id}}"
                   value="{{t1id}}" /></td>
        <td><label for="{{t1id}}">{{t1.name}}</label></td>
        <td>{{s1}}</td>
      </tr>
      <tr>
        <td><input type="checkbox" name="teams" id="{{t2id}}"
                   value="{{t2id}}" /></td>
        <td><label for="{{t2id}}">{{t2.name}}</label></td>
        <td>{{s2}}</td>
      </tr>
    %end
    </table>
  </div>
%end

</form>

