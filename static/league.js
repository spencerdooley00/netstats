document.addEventListener("DOMContentLoaded", () => {
  console.log("📦 League JS loaded");

  let teamChoices = null;
  let playerChoices = null;

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
        renderLeagueTables(data, season);
      })
      .catch(err => {
        console.error("❌ Failed to fetch league roles:", err);
        const container = document.getElementById("league-role-tables");
        container.innerHTML = `<p style="color:red;">Error loading data for ${season}</p>`;
      });
  }

  function renderLeagueTables(data, season) {
    const container = document.getElementById("league-role-tables");
    container.innerHTML = "";

    const grid = document.createElement("div");
    grid.className = "role-grid";
    container.appendChild(grid);

    const roles = [
      { key: "hubs", label: "Hubs" },
      { key: "sources", label: "Sources" },
      { key: "conduits", label: "Conduits" },
      { key: "sinks", label: "Sinks" },
      { key: "black_holes", label: "Black Holes" }
    ];

    const roleScoreKeys = {
      hubs: "hub",
      sources: "source",
      conduits: "conduit",
      sinks: "sink",
      black_holes: "black_hole"
    };

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
        </thead>`;

      const tbody = `
        <tbody>
          ${players.map((p, i) => `
            <tr class="${i >= 10 ? 'extra-row' : ''}" data-player="${p.player}" data-team="${p.team}">
              <td>${p.team}</td>
              <td>
                <a href="/player/${season}/${p.team}/${encodeURIComponent(p.player)}"
                  onclick="gtag('event', 'player_click', { player: '${p.player}', team: '${p.team}', season: '${season}' });">
                  ${p.player}
                </a>
              </td>
              <td>${p[`${roleScoreKeys[key]}_score`] !== undefined ? p[`${roleScoreKeys[key]}_score`].toFixed(3) : "-"}</td>
            </tr>
          `).join("")}
        </tbody>`;

      table.innerHTML = thead + tbody;
      tableWrapper.appendChild(table);
      section.appendChild(tableWrapper);
      grid.appendChild(section);

      toggle.addEventListener("click", () => {
        tableWrapper.classList.toggle("collapsed");
        toggle.textContent = tableWrapper.classList.contains("collapsed") ? "Expand" : "Collapse";

        const extraRows = tableWrapper.querySelectorAll("tr.extra-row");
        extraRows.forEach(row => {
          row.style.display = tableWrapper.classList.contains("collapsed") ? "none" : "";
        });
      });
    });

    // Strongest connections (always shown)
    const connections = data.strongest_connections;
    if (connections?.length > 0) {
      const section = document.createElement("div");
      section.className = "league-role-section strongest-connections";

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
      container.appendChild(section);
    }

    // 🔍 Filters
    const playerSearch = document.getElementById("player-search");
    const teamFilter = document.getElementById("team-filter");

    // Clean up old Choices instances
    if (teamChoices) teamChoices.destroy();
    if (playerChoices) playerChoices.destroy();

    teamChoices = new Choices(teamFilter, {
      removeItemButton: true,
      placeholder: true,
      placeholderValue: "Select teams...",
      searchEnabled: true,
      searchFields: ['label', 'value'],
      shouldSort: true,
      duplicateItemsAllowed: false,
      itemSelectText: ''
    });

    playerChoices = new Choices(playerSearch, {
      removeItemButton: true,
      placeholder: true,
      placeholderValue: "Search players...",
      searchEnabled: true,
      searchFields: ['label', 'value'],
      shouldSort: true,
      duplicateItemsAllowed: false,
      itemSelectText: ''
    });

    // Fill filters
    const playerSet = new Set();
    const teamSet = new Set();
    roles.forEach(({ key }) => {
      const players = data[key] || [];
      players.forEach(p => {
        playerSet.add(p.player);
        teamSet.add(p.team);
      });
    });

    teamChoices.setChoices(
      [...teamSet].sort().map(team => ({ value: team, label: team })),
      "value", "label", false
    );

    playerChoices.setChoices(
      [...playerSet].sort().map(player => ({ value: player, label: player })),
      "value", "label", false
    );

    // Apply filter logic
    function applyFilters() {
      const selectedPlayers = playerChoices.getValue(true);
      const selectedTeams = teamChoices.getValue(true);

      document.querySelectorAll(".league-role-table").forEach(table => {
        const rows = Array.from(table.querySelectorAll("tbody tr"));
        const matchingRows = rows.filter(row => {
          const team = row.dataset.team;
          const player = row.dataset.player;
          return (
            (selectedTeams.length === 0 || selectedTeams.includes(team)) &&
            (selectedPlayers.length === 0 || selectedPlayers.includes(player))
          );
        });

        rows.forEach(row => row.style.display = "none");
        matchingRows.forEach((row, i) => {
          row.style.display = i < 20 ? "" : "none";
          row.classList.toggle("extra-row", i >= 20);
        });

        const wrapper = table.closest(".table-wrapper");
        const toggle = wrapper?.previousElementSibling;
        if (toggle && toggle.classList.contains("expand-button")) {
          if (matchingRows.length > 20) {
            wrapper.classList.add("collapsed");
            toggle.textContent = "Expand";
            toggle.style.display = "inline-block";
          } else {
            wrapper.classList.remove("collapsed");
            toggle.textContent = "";
            toggle.style.display = "none";
          }
        }
      });
    }

    playerSearch.addEventListener("change", applyFilters);
    teamFilter.addEventListener("change", applyFilters);

    document.getElementById("reset-filters").addEventListener("click", () => {
      teamChoices.clearInput();
      teamChoices.removeActiveItems();
      playerChoices.clearInput();
      playerChoices.removeActiveItems();
      applyFilters();
    });
  }
});
