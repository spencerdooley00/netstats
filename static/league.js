document.addEventListener("DOMContentLoaded", () => {
  console.log("📦 League JS loaded");

  const seasonSelect = document.getElementById("season");
  if (!seasonSelect) {
    console.error("❌ Season dropdown not found.");
    return;
  }

  seasonSelect.addEventListener("change", () => {
    const season = seasonSelect.value;
    console.log("🔄 Season changed:", season);
    fetchLeagueRoles(season);
  });

  // Initial load
  fetchLeagueRoles(seasonSelect.value);
});

function fetchLeagueRoles(season) {
  console.log("📤 Fetching league roles for:", season);

  fetch("/league_roles", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ season })
  })
    .then(res => {
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return res.json();
    })
    .then(data => {
      console.log("✅ League role data received:", data);
      renderLeagueTables(data);
    })
    .catch(err => {
      console.error("❌ Failed to fetch league roles:", err);
      const container = document.getElementById("league-role-tables");
      container.innerHTML = `<p style="color:red;">Error loading data for ${season}</p>`;
    });
}

function renderLeagueTables(data) {
  const container = document.getElementById("league-role-tables");
  container.innerHTML = "";  // ✅ move this here

  const grid = document.createElement("div");
  grid.className = "role-grid";
  container.appendChild(grid);

  const roles = [
    { key: "top_hubs", label: "Top Hubs" },
    { key: "distributors", label: "Distributors" },
    { key: "finishers", label: "Finishers" },
    { key: "black_holes", label: "Black Holes" }
  ];

  roles.forEach(({ key, label }) => {
    const players = data[key];
    if (!players || players.length === 0) return;

    const section = document.createElement("div");
    section.className = "league-role-section";

    const heading = document.createElement("h2");
    heading.textContent = label;
    section.appendChild(heading);

    const toggle = document.createElement("button");
    toggle.textContent = "Expand";
    toggle.className = "expand-button";
    section.appendChild(toggle);

    const tableWrapper = document.createElement("div");
    tableWrapper.className = "table-wrapper collapsed";

    const table = document.createElement("table");
    table.className = "league-role-table";

    const thead = `
  <thead>
    <tr>
      <th>Team</th>
      <th>Player</th>
      <th>Score</th>
    </tr>
  </thead>
`;

const tbody = `
  <tbody>
    ${players.map((p, i) => `
      <tr class="${i >= 10 ? 'extra-row' : ''}">
        <td>${p.team}</td>
        <td>${p.player}</td>
        <td>${p.score !== undefined ? p.score.toFixed(3) : "-"}</td>
      </tr>
    `).join("")}
  </tbody>
`;


    table.innerHTML = thead + tbody;
    tableWrapper.appendChild(table);
    section.appendChild(tableWrapper);
grid.appendChild(section);  // Instead of container.appendChild

    toggle.addEventListener("click", () => {
      tableWrapper.classList.toggle("collapsed");
      toggle.textContent = tableWrapper.classList.contains("collapsed") ? "Expand" : "Collapse";
    });
  });

  // Strongest Connections — full table, no toggle
  const connections = data.strongest_connections;
  if (connections?.length > 0) {
const section = document.createElement("div");
section.className = "league-role-section wide";

const heading = document.createElement("h2");
heading.textContent = "Strongest Connections";
section.appendChild(heading);

const table = document.createElement("table");
table.className = "league-role-table";
table.innerHTML = `
  <thead><tr><th>Team</th><th>Passer</th><th>Receiver</th><th>Passes</th></tr></thead>
  <tbody>
    ${connections.map(d => `
      <tr>
        <td>${d.team || "—"}</td>
        <td>${d.from}</td>
        <td>${d.to}</td>
        <td>${d.passes.toFixed(2)}</td>
      </tr>
    `).join("")}
  </tbody>
`;


    section.appendChild(table);
grid.appendChild(section);  // Instead of container.appendChild
  }
}

