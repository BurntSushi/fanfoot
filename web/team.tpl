%rebase layout title='Team'

%include weeks cur_week=week, week_url=week_url

<ul class="options">
  <li>
    <a href="{{bench_url}}">{{"No bench" if bench else "Show bench"}}</a>
  </li>
  <li>
    <a href="{{detailed_url}}">{{"No details" if detailed else "Details"}}</a>
  </li>
</ul>

%for team, max_row, table in tables:
  <div class="table">
    <h2>{{team.lgconf.label}} :: {{team.name}}</h2>
    <table>
    %for row in table:
      %if len(row) >= 1 and row[0] == '*':
        %row = row[1:]
        <tr class="playing">
      %else:
        <tr>
      %end

      %if not row:
        <td colspan="{{max_row}}">&nbsp;</td>
      %else:
        %cell_type = 'th' if row[0] == 'Pos' else 'td'
        %for cell in row:
          <{{cell_type}}>{{cell}}</{{cell_type}}>
        %end
      %end
      </tr>
    %end
    </table>
  </div>
%end
