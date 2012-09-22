<ul class="options">
%for week in xrange(1, 18):
  %if cur_week == week:
    <li>{{week}}</li>
  %else:
    <li><a href="{{week_url(week)}}">{{week}}</a></li>
  %end
%end
</ul>

