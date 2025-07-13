panel.innerHTML = `
  <div class="player-card-header">
    <button id="close-panel-button" class="close-button">Close</button>
  </div>
  <div class="player-card-content">
    <img src="${d.img}" class="player-card-img" />
    <h3 class="player-card-name">${d.name}</h3>
  </div>
  <table class="player-card-table">
<tr><td><strong>PTS:</strong></td><td>${isFinite(stats.PTS) ? Number(stats.PTS).toFixed(1) : "-"}</td></tr>
<tr><td><strong>AST:</strong></td><td>${isFinite(stats.AST) ? Number(stats.AST).toFixed(1) : "-"}</td></tr>
<tr><td><strong>REB:</strong></td><td>${isFinite(stats.REB) ? Number(stats.REB).toFixed(1) : "-"}</td></tr>
<tr><td><strong>+/-:</strong></td><td>${isFinite(stats.PLUS_MINUS) ? Number(stats.PLUS_MINUS).toFixed(1) : "-"}</td></tr>
<tr><td><strong>MIN:</strong></td><td>${isFinite(stats.MIN) ? Number(stats.MIN).toFixed(1) : "-"}</td></tr>
<tr><td><strong>FG%:</strong></td><td>${isFinite(stats.FG_PCT) ? (Number(stats.FG_PCT) * 100).toFixed(1) + "%" : "-"}</td></tr>
<tr><td><strong>3FG%:</strong></td><td>${isFinite(stats.FG3_PCT) ? (Number(stats.FG3_PCT) * 100).toFixed(1) + "%" : "-"}</td></tr>

  </table>
`;




row.innerHTML = `
  <td>${formattedLineupName}</td>
  <td>${lineup.GP}</td>
  <td>${isFinite(lineup.MIN) ? Number(lineup.MIN).toFixed(0) : "-"}</td>
  <td>${lineup.FGM}</td>
  <td>${lineup.FGA}</td>
  <td>${isFinite(lineup.FG_PCT) ? (Number(lineup.FG_PCT) * 100).toFixed(1) + "%" : "-"}</td>
  <td>${lineup.FG3M}</td>
  <td>${lineup.FG3A}</td>
  <td>${isFinite(lineup.FG3_PCT) ? (Number(lineup.FG3_PCT) * 100).toFixed(1) + "%" : "-"}</td>
  <td>${lineup.OREB}</td>
  <td>${lineup.DREB}</td>
  <td>${lineup.REB}</td>
  <td>${lineup.AST}</td>
  <td>${lineup.TOV}</td>
  <td>${lineup.STL}</td>
  <td>${lineup.BLK}</td>
  <td>${lineup.PTS}</td>
  <td>${lineup.PLUS_MINUS}</td>
`;