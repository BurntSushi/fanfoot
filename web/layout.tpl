<!doctype html>
<!--[if lt IE 7]> <html class="no-js lt-ie9 lt-ie8 lt-ie7" lang="en"> <![endif]-->
<!--[if IE 7]>    <html class="no-js lt-ie9 lt-ie8" lang="en"> <![endif]-->
<!--[if IE 8]>    <html class="no-js lt-ie9" lang="en"> <![endif]-->
<!--[if gt IE 8]><!--> <html class="no-js" lang="en"> <!--<![endif]-->
<head>
  <meta charset="iso-8859-1">
  <title>Andrew Gallant</title>
  <meta name="description" content="Andrew Gallant's fantasy homepage.">
  <meta name="viewport" content="width=device-width">
  %if not get('norefresh', False):
    <meta http-equiv="refresh" content="15">
  %end

  <link rel="stylesheet" href="/static/css/normalize.css">
  <link rel="stylesheet" href="/static/css/style.css">
  <link rel="stylesheet" href="/static/css/print.css">
</head>
<body>
  <div id="container"><div id="container2">
  <!-- <header>
    <h1>Fantasy 2012 :: {{title}}</h1>
  </header> -->
  <div id="content-cont">
    <div id="content" role="main">

    %include

    </div>
  </div>

  <div style="clear: both;"><br></div>

  <footer>
    <h3>Quick links</h3>
    <ul>
      <li>{{!url('Home', 'home')}}</li>
      <li>
        %lgteams = 'espn:2,keeper:11,pub1:8,pub2:7'
        {{!url('Langdon Algers', 'team', league_teams=lgteams)}}
        ({{!url('plays', 'plays', league_teams=lgteams)}})
      </li>
      <li>
        %lgteams = 'espn:1,keeper:10'
        {{!url('Smalls', 'team', league_teams=lgteams)}}
        ({{!url('plays', 'plays', league_teams=lgteams)}})
      </li>
    </ul>
  </footer>
  </div></div>
</body>
</html>

