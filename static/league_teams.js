document.addEventListener("DOMContentLoaded", () => {
  const seasonSelect = document.getElementById("season");
  const tableContainer = document.getElementById("team-metrics-table");

  function fetchTeamMetrics(season) {
    fetch("/team_metrics", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ season })
    })
    .then(res => res.json())
    .then(data => {
      renderTeamMetricsTable(data);
    })
    .catch(err => {
      console.error("Error loading team metrics:", err);
      tableContainer.innerHTML = `<p style="color:red;">Failed to load data for ${season}</p>`;
    });
  }

function renderTeamMetricsTable(data) {
  const headers = ["Team", "Entropy", "Flux", "Clustering", "Centralization", "Avg Path", "Passes"];
  let html = `<table id="team-metrics" class="league-role-table sortable"><thead><tr>`;

  headers.forEach(h => {
    html += `<th data-sort="${h.toLowerCase().replace(" ", "_")}">${h}</th>`;
  });
  html += `</tr></thead><tbody>`;

 Object.entries(data).forEach(([team, metrics]) => {
  const teamLink = `/team_explorer/${team}/${seasonSelect.value}`;
  html += `<tr>
    <td><a href="${teamLink}" class="team-link">${team}</a></td>
    <td>${metrics.entropy.toFixed(2)}</td>
    <td>${metrics.flux.toFixed(2)}</td>
    <td>${metrics.clustering.toFixed(3)}</td>
    <td>${metrics.centralization.toFixed(2)}</td>
    <td>${metrics.avg_path_len?.toFixed(2) ?? "-"}</td>
    <td>${metrics.num_passes.toFixed(0)}</td>
  </tr>`;
});

  html += `</tbody></table>`;
  tableContainer.innerHTML = html;

  makeTableSortable(document.getElementById("team-metrics"));
}
function makeTableSortable(table) {
  const headers = Array.from(table.querySelectorAll("thead th"));
  let sortDirection = {};

  headers.forEach((th, colIndex) => {
    th.addEventListener("click", () => {
      const key = th.textContent.trim();
      const ascending = !sortDirection[key];
      sortDirection[key] = ascending;

      const rows = Array.from(table.querySelectorAll("tbody tr"));
      rows.sort((a, b) => {
        const valA = a.children[colIndex].textContent.trim();
        const valB = b.children[colIndex].textContent.trim();

        const numA = parseFloat(valA);
        const numB = parseFloat(valB);

        if (!isNaN(numA) && !isNaN(numB)) {
          return ascending ? numA - numB : numB - numA;
        } else {
          return ascending ? valA.localeCompare(valB) : valB.localeCompare(valA);
        }
      });

      const tbody = table.querySelector("tbody");
      rows.forEach(row => tbody.appendChild(row));
    });
  });
}

  seasonSelect.addEventListener("change", () => {
    fetchTeamMetrics(seasonSelect.value);
  });

  document.getElementById("reset-filters").addEventListener("click", () => {
    seasonSelect.selectedIndex = 0;
    fetchTeamMetrics(seasonSelect.value);
  });

  fetchTeamMetrics(seasonSelect.value);
});
