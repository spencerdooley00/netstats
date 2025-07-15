// team.js
import { courtSvgHtml } from './courtSvg.js';

document.addEventListener("DOMContentLoaded", () => {
  const TEAM_ID_LOOKUP = {
    ATL: 1610612737, BOS: 1610612738, BKN: 1610612751, CHA: 1610612766, CHI: 1610612741,
    CLE: 1610612739, DAL: 1610612742, DEN: 1610612743, DET: 1610612765, GSW: 1610612744,
    HOU: 1610612745, IND: 1610612754, LAC: 1610612746, LAL: 1610612747, MEM: 1610612763,
    MIA: 1610612748, MIL: 1610612749, MIN: 1610612750, NOP: 1610612740, NYK: 1610612752,
    OKC: 1610612760, ORL: 1610612753, PHI: 1610612755, PHX: 1610612756, POR: 1610612757,
    SAC: 1610612758, SAS: 1610612759, TOR: 1610612761, UTA: 1610612762, WAS: 1610612764
  };


  document.querySelectorAll(".tab").forEach(tab => {
    tab.addEventListener("click", () => {
      const tabName = tab.dataset.tab;
      switchTab(tabName);
    });
  });

  let currentLineupShots = [];
  let currentAssistNetworkData = null;
  let currentPlayerFilter = null;
  let shots = [];

 function switchTab(tabName) {
  document.querySelectorAll(".tab-button").forEach(b => b.classList.remove("active"));
  document.querySelector(`.tab-button[data-tab="${tabName}"]`)?.classList.add("active");

  document.querySelectorAll(".tab-content").forEach(tab => {
    tab.style.display = "none";
  });
  const activeTab = document.getElementById(`${tabName}-tab`);
  if (activeTab) activeTab.style.display = "block";

  const sidebar = document.querySelector(".sidebar");
  const lineupTable = document.getElementById("lineup-table");

  if (tabName === "lineup") {
    if (sidebar) sidebar.style.display = "none";
    if (lineupTable) {
      lineupTable.style.display = "block";
      lineupTable.style.opacity = 0;
      setTimeout(() => lineupTable.style.opacity = 1, 10);
    }
    fetchAndRenderTopLineups();
  } else {
    if (sidebar) sidebar.style.display = "block";
    if (lineupTable) lineupTable.style.display = "none";
  }

  // ✨ NEW — Reset player card when leaving or re-entering passing tab
  const rightPanel = document.getElementById("right-panel");
  if (rightPanel && tabName !== "passing") {
    rightPanel.style.display = "none";
rightPanel.style.display = "none";
  }

  if (tabName === "passing") {
  currentPlayerFilter = null;  // ✅ Clear Lineup tab player filter
  updatePassingNetwork(true);
}
  if (tabName === "assist" && currentAssistNetworkData) drawAssistNetwork(currentAssistNetworkData);
}




document.querySelectorAll(".tab-button").forEach(btn => {
  btn.addEventListener("click", (e) => {
    const tabName = btn.dataset.tab;
    if (!tabName) return;  // ignore buttons without tab data (e.g., "Back to Home")

    e.preventDefault();
    switchTab(tabName);
  });
});


function handleTeamOrSeasonChange() {
  console.log("SEASON CHANGE");

  const activeTab = document.querySelector(".tab-button.active")?.dataset.tab;
  if (activeTab === "lineup") {
    console.log("→ Updating lineup view");
    fetchAndRenderTopLineups();
  } else {
    console.log("→ Updating passing network");
    updatePassingNetwork(false);
  }
}

// document.getElementById("team").addEventListener("change", handleTeamOrSeasonChange);
// document.getElementById("season").addEventListener("change", handleTeamOrSeasonChange);


// NEW
function drawHeatmap(data, selector) {
  const g = d3.select(selector).select("g.court-g");
  if (g.empty()) {
    console.warn(`❌ drawHeatmap aborted — ${selector} g.court-g not found`);
    return;
  }

  g.selectAll(".shot").remove();

  const heat = d3.contourDensity()
    .x(d => (d.LOC_X * 0.86) + 215.5)
    .y(d => (d.LOC_Y * 0.86) + 41.4)
    .size([431, 405.14])
    .bandwidth(20)(data);

  g.selectAll("path.heat")
    .data(heat)
    .join("path")
    .attr("class", "shot heat")
    .attr("d", d3.geoPath())
    .attr("fill", "orange")
    .attr("opacity", d => d.value * 8);
}
// NEW
function drawHexbins(data, selector) {
  const g = d3.select(selector).select("g.court-g");
  if (g.empty()) {
    console.warn(`⚠️ ${selector} g.court-g not ready`);
    return;
  }

  g.selectAll(".shot").remove();

  const hexbin = d3.hexbin()
    .x(d => (d.LOC_X * 0.86) + 215.5)
    .y(d => (d.LOC_Y * 0.86) + 41.4)
    .radius(12)
    .extent([[0, 0], [431, 405.14]]);

  const bins = hexbin(data);

  const binStats = bins.map(bin => {
const makes = bin.filter(d => Number(d.SHOT_MADE_FLAG) === 1).length;
    const attempts = bin.length;
    const fgPct = attempts > 0 ? makes / attempts : 0;
    return { bin, makes, attempts, fgPct, x: bin.x, y: bin.y };
  });

  const maxAttempts = d3.max(binStats, d => d.attempts);

  // const radiusScale = d3.scaleSqrt().domain([0, maxAttempts]).range([0, 12]);
  // const radiusScale = d3.scaleSqrt().domain([0, maxAttempts]).range([0, 12]);
  const radiusScale = d3.scaleSqrt().domain([0, maxAttempts]).range([3, 14]); 
  const color = d3.scaleLinear().domain([0.0, 1.0]).range(["#444", "#f97316"]);

  const tooltip = d3.select("body").append("div").attr("class", "tooltip").style("opacity", 0);

  g.selectAll("path.hex")
    .data(binStats)
    .enter()
    .append("path")
    .attr("class", "shot hex")
    .attr("d", d => hexbin.hexagon(radiusScale(d.attempts)))
    .attr("transform", d => `translate(${d.x},${d.y})`)
    .attr("fill", d => color(d.fgPct))
.attr("opacity", d => 0.3 + 0.5 * (d.attempts / maxAttempts))
.attr("stroke", "#1f2937")
.attr("stroke-width", 0.6)
    .on("mouseover", function (event, d) {
      d3.select(this).attr("stroke", "#facc15").attr("stroke-width", 2);
      tooltip.transition().duration(200).style("opacity", 1);
      tooltip.html(`
        <strong>FG%:</strong> ${(d.fgPct * 100).toFixed(1)}%<br/>
        <strong>FGM:</strong> ${d.makes}<br/>
        <strong>FGA:</strong> ${d.attempts}
      `)
      .style("left", (event.pageX + 12) + "px")
      .style("top", (event.pageY - 28) + "px");
    })
    .on("mouseout", function () {
      d3.select(this).attr("stroke", "#ffffff22").attr("stroke-width", 1);
      tooltip.transition().duration(200).style("opacity", 0);
    });
}
// NEW
function renderShots(data, selector, togglePrefix = null) {
  const heatToggleId = togglePrefix ? `#${togglePrefix}-heatmap-toggle` : "#heatmap-toggle";
  const makesToggleId = togglePrefix ? `#${togglePrefix}-makes-only-toggle` : "#makes-only-toggle";

  const heat = document.querySelector(heatToggleId)?.checked;
  const makes = document.querySelector(makesToggleId)?.checked;

  let filtered = data;
  if (currentPlayerFilter) {
    filtered = filtered.filter(d => d.PLAYER_NAME?.trim().toLowerCase() === currentPlayerFilter.trim().toLowerCase());
  }
  if (makes) {
  filtered = filtered.filter(d => Number(d.SHOT_MADE_FLAG) === 1);
  }
console.log("heat:", heat, "makes:", makes, "filtered length:", filtered.length);
console.log("SHOT_MADE_FLAG values:", [...new Set(filtered.map(s => s.SHOT_MADE_FLAG))]);

  heat ? drawHeatmap(filtered, selector) : drawHexbins(filtered, selector);
}

function renderFlowLinks(svgGroup, links) {
  const tooltip = d3.select("body").append("div").attr("class", "tooltip").style("opacity", 0);
  const defs = svgGroup.append("defs");

  // Gradients
  links.forEach((d) => {
    const id = `grad-${d.source.id}-${d.target.id}`.replace(/\s+/g, "-");
    const grad = defs.append("linearGradient")
      .attr("id", id)
      .attr("gradientUnits", "userSpaceOnUse");

    // Decide who passes more
    const fromA = d.a2b >= d.b2a;
    d.dominantSource = fromA ? d.source : d.target;
    d.dominantTarget = fromA ? d.target : d.source;
    d.dominantShare = fromA ? d.a2b / d.weight : d.b2a / d.weight;

    grad.append("stop")
      .attr("offset", "0%")
      .attr("stop-color", "#007bff");

    grad.append("stop")
      .attr("offset", `${(d.dominantShare * 100).toFixed(1)}%`)
      .attr("stop-color", "#ffffff");

    grad.append("stop")
      .attr("offset", "100%")
      .attr("stop-color", "#ffffff");
  });

  // Edge lines
  const link = svgGroup.append("g")
    .attr("class", "flow-links")
    .selectAll("line")
    .data(links)
    .enter().append("line")
    .attr("stroke-width", d => Math.max(2, d.weight ** 0.75))
    .attr("stroke-opacity", 0.95)
    .attr("stroke", d => `url(#grad-${d.source.id}-${d.target.id}`.replace(/\s+/g, "-") + ")");

  // Tooltip
  function formatTooltip(d) {
    const a = d.source.name || d.source;
    const b = d.target.name || d.target;
    return `
      <strong>${a} ↔ ${b}</strong><br>
      ${a} → ${b}: ${d.a2b.toFixed(1)}<br>
      ${b} → ${a}: ${d.b2a.toFixed(1)}<br>
      Total: ${d.weight.toFixed(1)}
    `;
  }

  link
    .on("mouseover", (event, d) => {
      tooltip.transition().duration(200).style("opacity", 0.95);
      tooltip.html(formatTooltip(d))
        .style("left", (event.pageX + 12) + "px")
        .style("top", (event.pageY - 20) + "px");
    })
    .on("mouseout", () => tooltip.transition().duration(200).style("opacity", 0));

  return { linkA: link, linkB: link };
}


// function renderFlowLinks(svgGroup, links) {
//   const tooltip = d3.select("body").append("div").attr("class", "tooltip").style("opacity", 0);

//   // === Define Gradients ===
//   const defs = svgGroup.append("defs");

//   links.forEach((d, i) => {
//     const id = `grad-${d.source.id}-${d.target.id}`.replace(/\s+/g, "-");
//     const grad = defs.append("linearGradient")
//       .attr("id", id)
//       .attr("gradientUnits", "userSpaceOnUse")
//       .attr("x1", 0)
//       .attr("y1", 0)
//       .attr("x2", 100)
//       .attr("y2", 0); // Will be overridden dynamically per line

//     const pctA = d.a2b / d.weight;
//     const pctB = d.b2a / d.weight;

//     grad.append("stop")
//       .attr("offset", "0%")
//       .attr("stop-color", pctA >= pctB ? "#007bff" : "#facc15");

//     grad.append("stop")
//       .attr("offset", `${Math.round(pctA * 100)}%`)
//       .attr("stop-color", "#ffffff");

//     grad.append("stop")
//       .attr("offset", "100%")
//       .attr("stop-color", pctA < pctB ? "#007bff" : "#facc15");
//   });

//   // === Draw gradient edges ===
//   const link = svgGroup.append("g")
//     .attr("class", "flow-links")
//     .selectAll("line")
//     .data(links)
//     .enter().append("line")
//     .attr("stroke-width", d => Math.max(1, d.weight ** 0.6))
//     .attr("stroke-opacity", 0.95)
//     .attr("stroke", d => `url(#grad-${d.source.id}-${d.target.id}`.replace(/\s+/g, "-") + ")");

//   function formatTooltip(d) {
//     const a = d.source.name || d.source;
//     const b = d.target.name || d.target;
//     return `
//       <strong>${a} ↔ ${b}</strong><br>
//       ${a} → ${b}: ${d.a2b.toFixed(1)}<br>
//       ${b} → ${a}: ${d.b2a.toFixed(1)}<br>
//       Total: ${d.weight.toFixed(1)}
//     `;
//   }

//   link.on("mouseover", (event, d) => {
//     tooltip.transition().duration(200).style("opacity", 0.95);
//     tooltip.html(formatTooltip(d))
//       .style("left", (event.pageX + 12) + "px")
//       .style("top", (event.pageY - 20) + "px");
//   }).on("mouseout", () => tooltip.transition().duration(200).style("opacity", 0));

//   return {
//     linkA: link, // reuse the same key so `simulation.on("tick")` still works
//     linkB: link
//   };
// }



function renderDirectionalLinks(svgGroup, links) {
  const tooltip = d3.select("body").append("div").attr("class", "tooltip").style("opacity", 0);

  const link = svgGroup.append("g")
    .selectAll("path")
    .data(links)
    .enter().append("path")
  .attr("class", "passing-link")  // ✅ Add this
  .attr("data-source", d => d.source.id || d.source)
  .attr("data-target", d => d.target.id || d.target)
    .attr("stroke", d => d3.interpolate("rgba(0, 135, 255, 1)", "#facc15")(Math.min(1, d.weight / 10)))
    .attr("stroke-width", d => d.weight ** 0.8)
    .attr("opacity", 0.9)
    .attr("fill", "none")
    .attr("marker-end", "url(#arrow)");

  link
    .on("mouseover", function (event, d) {
      d3.select(this)
        .raise()
        .transition()
        .duration(100)
        .attr("stroke-width", d => d.weight ** 0.8 + 2.5)
        .attr("stroke", "#ffA500");

      tooltip.transition().duration(200).style("opacity", 0.95);
      tooltip.html(`<strong>${d.source.name} → ${d.target.name}</strong><br>Passes: ${d.weight}`)
        .style("left", (event.pageX + 12) + "px")
        .style("top", (event.pageY - 20) + "px");
    })
    .on("mouseout", function () {
      d3.select(this)
        .transition()
        .duration(100)
        .attr("stroke", d => d3.interpolate("rgba(0, 135, 255, 1)", "#facc15")(Math.min(1, d.weight / 10)))
        .attr("stroke-width", d => d.weight ** 0.8 + 2.5)
        .attr("opacity", 0.9);

      tooltip.transition().duration(200).style("opacity", 0);
    });

  return link;
}

function handleNodeClick(event, d) {
  const season = document.getElementById("season").value;
  const team = document.getElementById("team").value;
  const rightPanel = document.getElementById("right-panel");

  if (!rightPanel) {
    console.warn("⚠️ right-panel not found in DOM!");
    return;
  }

  rightPanel.style.display = "block";

  const panel = document.getElementById("player-details");
  const stats = d.stats || {};
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

  // Close panel button listener
  document.getElementById("close-panel-button")?.addEventListener("click", () => {
    document.getElementById("right-panel").style.display = "none";
  });

  let svgContainer = document.getElementById("court-svg-container");

// 🔧 If it doesn't exist (maybe removed by tab switch), recreate it
if (!svgContainer) {
  const rightPanel = document.getElementById("right-panel");
  svgContainer = document.createElement("div");
  svgContainer.id = "court-svg-container";
  rightPanel.appendChild(svgContainer);
} else {
  svgContainer.innerHTML = "";
}

// Always rebuild court SVG
const courtSvg = d3.select(svgContainer)
  .append("svg")
  .attr("id", "court-svg")
  .attr("width", 431)
  .attr("height", 405.14)
  .attr("viewBox", "0 0 431 405.14");

courtSvg.html(courtSvgHtml);


  const g = courtSvg.select("g.court-g");
  if (g.empty()) {
    console.warn("❌ g.court-g missing");
    return;
  }

  // Fetch & render shot data
  fetch("/player_shots", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ player: d.name, season, team })
  })
    .then(res => res.json())
    .then(data => {
      shots = data; // store globally
      renderShots(shots, "#court-svg");

// Just attach event listeners if not already added
const heatToggle = document.getElementById("heatmap-toggle");
const makesToggle = document.getElementById("makes-only-toggle");

if (heatToggle && !heatToggle.dataset.bound) {
  heatToggle.addEventListener("change", () => renderShots(shots, "#court-svg"));
  heatToggle.dataset.bound = "true";
}

if (makesToggle && !makesToggle.dataset.bound) {
  makesToggle.addEventListener("change", () => renderShots(shots, "#court-svg"));
  makesToggle.dataset.bound = "true";
}

// 🔥 DO NOT reset the .checked values — preserve toggle state
renderShots(shots, "#court-svg");

    });
}





  // Passing Network Logic — like index.js
 function updatePassingNetwork(preservePlayers = false) {
  const season = document.getElementById("season").value;
  const team = document.getElementById("team").value;

  const players = preservePlayers
    ? Array.from(document.querySelectorAll("#player-checkboxes input[type='checkbox']:checked")).map(cb => cb.value)
    : undefined;

  console.log("Sending updatePassingNetwork", { season, team, players });  // ✅ Debug log

  fetch("/update_network", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ season, team, players })
  })
    .then(res => res.json())
    .then(data => {
      const checkboxContainer = document.getElementById("player-checkboxes");
      checkboxContainer.innerHTML = "";

      data.players.forEach(player => {
        const label = document.createElement("label");
        label.className = "player-checkbox";

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.value = player;
        if (data.selected.includes(player)) {
          checkbox.checked = true;
          label.classList.add("checked");
        }

        const customBox = document.createElement("span");
        customBox.className = "custom-checkbox";

        const nameSpan = document.createElement("span");
        nameSpan.className = "player-name";
        nameSpan.textContent = player;

        label.appendChild(checkbox);
        label.appendChild(customBox);
        label.appendChild(nameSpan);
        checkboxContainer.appendChild(label);

        checkbox.addEventListener("change", () => {
          label.classList.toggle("checked", checkbox.checked);
          updatePassingNetwork(true);
        });
      });

      // Only draw network if tab is active
      const passingTab = document.querySelector(".tab-button[data-tab='passing']");
      if (passingTab && passingTab.classList.contains("active")) {
        drawPassingNetwork(data);
        window.currentNetworkData = data;
document.getElementById("flow-toggle")?.addEventListener("change", () => {
  if (!window.currentNetworkData) return;

  drawPassingNetwork(window.currentNetworkData);  // Rebuilds the network

  // If player panel is open and we have shots, re-render chart
  const panelVisible = document.getElementById("right-panel")?.style.display !== "none";
  if (!panelVisible || !shots?.length) return;

  const container = document.getElementById("court-svg-container");
  if (!container) return;

  // 1. Clear and re-add court SVG
  container.innerHTML = "";
  const courtSvg = d3.select(container)
    .append("svg")
    .attr("id", "court-svg")
    .attr("width", 431)
    .attr("height", 405.14)
    .attr("viewBox", "0 0 431 405.14");

  courtSvg.html(courtSvgHtml);  // Adds court SVG markup

  // 2. Wait for g.court-g to appear, then render
  let tries = 0;
  function tryRender() {
    const g = d3.select("#court-svg").select("g.court-g");
    if (!g.empty()) {
      renderShots(shots, "#court-svg");  // ✅ Renders with toggle state
    } else if (tries < 10) {
      tries++;
      setTimeout(tryRender, 30);
    } else {
      console.warn("❌ Flow toggle: g.court-g not ready after multiple attempts");
    }
  }
  tryRender();
});


      }
    });
}

function drawPassingNetwork(data) {
  d3.select("#passing-tab").selectAll("svg").remove();
  const isFlow = document.getElementById("flow-toggle")?.checked;

  let links = data.links;
  const width = document.getElementById("passing-tab").clientWidth;
  const height = window.innerHeight;

  const svg = d3.select("#network").append("svg")
    .attr("width", width + 400)
    .attr("height", height - 100);

  svg.append("defs").append("marker")
    .attr("id", "arrow")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 60)
    .attr("refY", -4)
    .attr("markerWidth", 8)
    .attr("markerHeight", 8)
    .attr("orient", "auto")
    .attr("markerUnits", "userSpaceOnUse")
    .append("path")
    .attr("d", "M0,-5L10,0L0,5")
    .attr("fill", "#666");

  const svgGroup = svg.append("g").attr("transform", `translate(-70,70)`);

  svg.call(d3.zoom().scaleExtent([0.5, 2]).on("zoom", (event) => {
    svgGroup.attr("transform", event.transform);
  }));

  const simulation = d3.forceSimulation(data.nodes)
    .force("link", d3.forceLink(data.links).id(d => d.id).distance(500))
    .force("charge", d3.forceManyBody().strength(-400))
    .force("center", d3.forceCenter(width / 2 - 150, height / 2 - 150))
    .force("collide", d3.forceCollide().radius(75))
    .force("x", d3.forceX(width / 2).strength(0.001))
    .force("y", d3.forceY(height / 2).strength(0.09));

  // === FLOW VS NON-FLOW ===
  let link, linkA, linkB;
  if (isFlow) {
    const combinedMap = new Map();
    data.links.forEach(link => {
      const sourceId = typeof link.source === "object" ? link.source.id : link.source;
      const targetId = typeof link.target === "object" ? link.target.id : link.target;
      const key = [sourceId, targetId].sort().join("-");

      if (!combinedMap.has(key)) {
        combinedMap.set(key, {
          source: link.source,
          target: link.target,
          weight: 0,
          a2b: 0,
          b2a: 0
        });
      }

      const entry = combinedMap.get(key);
      const isAB = sourceId < targetId;
      if (isAB) entry.a2b += +link.weight;
      else entry.b2a += +link.weight;
      entry.weight = entry.a2b + entry.b2a;
    });

    links = Array.from(combinedMap.values());
    ({ linkA, linkB } = renderFlowLinks(svgGroup, links));
  } else {
    link = renderDirectionalLinks(svgGroup, data.links);
  }

  // === NODES ===
  const node = svgGroup.append("g")
    .selectAll("g")
    .data(data.nodes)
    .enter().append("g");

  node.append("clipPath")
    .attr("id", d => `clip-${d.id.replace(/\s+/g, "-")}`)
    .append("circle")
  .attr("r", 40)            // increase radius to show more face
  .attr("cx", 0)
  .attr("cy", 0);

node.append("image")
  .attr("xlink:href", d => d.img)
  .attr("width", 80)        // match visible area

    .attr("height", 80)
    .attr("x", -40)
    .attr("y", -40)
    .attr("clip-path", d => `url(#clip-${d.id.replace(/\s+/g, "-")})`)
    .attr("pointer-events", "visible");

  node.append("text")
    .text(d => d.name)
    .attr("text-anchor", "middle")
    .attr("dy", 40)
    .attr("font-size", "12px")
    .attr("fill", "#FFFFFF");

  const tooltip = d3.select("body").append("div")
    .attr("class", "tooltip")
    .style("opacity", 0);

  // === ON NODE CLICK ===
  node.on("mouseover", (event, d) => {
  if (!isFlow) {
    const playerId = d.id;

    d3.selectAll("path.passing-link")
      .attr("opacity", l => {
        const source = l.source.id || l.source;
        const target = l.target.id || l.target;
        return (source === playerId || target === playerId) ? 1 : 0;
      })
      .attr("stroke", l => {
        const source = l.source.id || l.source;
        const target = l.target.id || l.target;
        if (source === playerId) return "#3b82f6";  // blue
        if (target === playerId) return "#facc15";  // yellow
        return "none";
      });
  }

  tooltip.transition().duration(200).style("opacity", 0.9);
  tooltip.html(`<strong>${d.name}</strong>`)
    .style("left", (event.pageX + 10) + "px")
    .style("top", (event.pageY - 20) + "px");
});

node.on("mouseout", () => {
  tooltip.transition().duration(300).style("opacity", 0);

  if (!isFlow) {
    d3.selectAll("path.passing-link")
      .attr("opacity", 0.9)
      .attr("stroke", d => d3.interpolate("rgba(0, 135, 255, 1)", "#facc15")(Math.min(1, d.weight / 10)));
  }
});


  node.on("click", handleNodeClick);

simulation.on("tick", () => {
  node.attr("transform", d => `translate(${d.x},${d.y})`);

  if (isFlow && linkA) {
    linkA
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y)
      .attr("stroke-width", d => Math.max(2, d.weight ** 0.75));

    links.forEach(d => {
      d3.select(`#grad-${d.source.id}-${d.target.id}`.replace(/\s+/g, "-"))
        .attr("x1", d.dominantSource.x)
        .attr("y1", d.dominantSource.y)
        .attr("x2", d.dominantTarget.x)
        .attr("y2", d.dominantTarget.y);
    });
  }

  if (!isFlow && link) {
    link.attr("d", d => {
      const dx = d.target.x - d.source.x;
      const dy = d.target.y - d.source.y;
      const dr = Math.sqrt(dx * dx + dy * dy) * 1.5;
      return `M${d.source.x},${d.source.y}A${dr},${dr} 0 0,1 ${d.target.x},${d.target.y}`;
    });
  }
});



}
 
function updateAssistNetwork(lineup) {
  const season = document.getElementById("season").value;
  const team = document.getElementById("team").value;

  fetch("/update_assist_network", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ season, team, lineup })
  })
    .then(res => res.json())
    .then(data => {
      currentAssistNetworkData = data;
      drawNetwork(data, "#assist-network"); // ✅ Provide correct selector
    })
    .catch(err => {
      console.error("Error fetching assist network:", err);
    });
}

function drawNetwork(data) {
d3.select("#assist-network").selectAll("*").remove();


const netDiv = document.getElementById("passing");
const container = document.querySelector("#assist-network");
if (!container) {
  console.warn("drawNetwork aborted — #assist-network not found.");
  return;
}const width = container.clientWidth || 800;
const height = container.clientHeight || 600;

if (width === 0 || height === 0) {
  console.warn("Fallback width/height used");
  width = 800;
  height = 600;
}

if (!data || !Array.isArray(data.nodes) || !Array.isArray(data.links)) {
  console.error("Invalid data passed to drawNetwork:", data);
  return;
}

if (width < 100 || height < 100) {
  console.warn("Network draw aborted — container size not ready yet");
  return;
}


console.log("Drawing network with data:", data);
console.log("Nodes:", data.nodes);
console.log("Links:", data.links);
const links = data.links;


if (width === 0 || height === 0) {
  console.warn("drawNetwork called before layout ready");
}


  const svg = d3.select("#assist-network").append("svg")
  .attr("width", width)
  .attr("height", height);

  // ✅ Add this
  svg.append("defs").append("marker")
    .attr("id", "arrow")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 60)
    .attr("refY", -4)
    .attr("markerWidth", 8)
    .attr("markerHeight", 8)
    .attr("orient", "auto")
    .attr("markerUnits", "userSpaceOnUse")
    .append("path")
    .attr("d", "M0,-5L10,0L0,5")
    .attr("fill", "#666");

  const svgGroup = svg.append("g").attr("transform", "translate(60, 60)");
//   svg.call(d3.zoom().scaleExtent([0.5, 2]).on("zoom", e => svgGroup.attr("transform", e.transform)));

data.nodes.forEach(d => {
  d.x = width / 2 + Math.random() * 100;
  d.y = height / 2 + Math.random() * 100;
});

const simulation = d3.forceSimulation(data.nodes)
  .force("link", d3.forceLink(links).id(d => d.id).distance(350))
  .force("charge", d3.forceManyBody().strength(-600))
  .force("collide", d3.forceCollide().radius(90))
  .force("center", d3.forceCenter((width - 120) / 2, (height - 120) / 2));

simulation.alpha(1).restart();

  const tooltip = d3.select("body").append("div")
    .attr("class", "tooltip").style("opacity", 0);
console.log("Appending links and nodes", data.nodes.length, data.links.length);

  const link = svgGroup.append("g")
  .selectAll("path")
    .data(data.links)
    .enter().append("path")
.attr("stroke", d => d3.interpolate("rgba(0, 135, 255, 1)", "#facc15")(Math.min(1, d.weight / 10)))
.attr("stroke-width", d => d.weight ** 0.5)
.attr("opacity", 0.9)

    .attr("fill", "none")
    .attr("marker-end", "url(#arrow)")
    .on("mouseover", function (event, d) {
      d3.select(this).raise().transition().duration(100).attr("stroke", "#facc15").attr("stroke-width", 5);
      tooltip.transition().duration(200).style("opacity", 0.95);
      tooltip.html(`<strong>${d.source.name} → ${d.target.name}</strong><br>Assists: ${d.weight}`)
        .style("left", (event.pageX + 12) + "px").style("top", (event.pageY - 20) + "px");
    })
    .on("mouseout", function () {
      d3.select(this).transition().duration(100)
      .attr("stroke", d => d3.interpolate("rgba(0, 135, 255, 1)", "#facc15")(Math.min(1, d.weight / 10)))
.attr("stroke-width", d => d.weight ** 0.5)
        // .attr("stroke", "rgba(96, 165, 250, 0.85)")  // Tailwind's `blue-400`

        // .attr("stroke-width", d => d.weight ** 0.6);
      tooltip.transition().duration(200).style("opacity", 0);
    });

  const node = svgGroup.append("g").selectAll("g")
    .data(data.nodes).enter().append("g");

node.append("clipPath")
  .attr("id", d => `clip-${d.id.replace(/\s+/g, "-")}`)
  .append("circle").attr("r", 36).attr("cx", 0).attr("cy", 0);

node.append("circle")
  .attr("r", 40)
  .attr("fill", "none")
  .attr("stroke", "#facc15")
  .attr("stroke-width", 2);

node.append("image")
  .attr("xlink:href", d => d.img)
  .attr("width", 100).attr("height", 100)
  .attr("x", -50).attr("y", -50)
  .attr("clip-path", d => `url(#clip-${d.id.replace(/\s+/g, "-")})`);

  node.append("text")
    .text(d => d.name)
    .attr("text-anchor", "middle")
    .attr("dy", 60)
    .attr("font-size", "12px")
    .attr("fill", "#FFFFFF");

    
  node.on("click", (event, d) => {
  currentPlayerFilter = d.name;
    console.log("✅ Set currentPlayerFilter to:", currentPlayerFilter);
waitForCourtAndRender(currentLineupShots, "#assist-court-svg", 10, "assist");

  // renderShots(currentLineupShots);
});


  simulation.on("tick", () => {
    link.attr("d", d => {
      const dx = d.target.x - d.source.x;
      const dy = d.target.y - d.source.y;
      const dr = Math.sqrt(dx * dx + dy * dy) * 1.5;
      return `M${d.source.x},${d.source.y}A${dr},${dr} 0 0,1 ${d.target.x},${d.target.y}`;
    });

    node.attr("transform", d => `translate(${d.x},${d.y})`);
  });
}
function updateLineupShotChart(lineup) {
  const season = document.getElementById("season").value;
  const team = document.getElementById("team").value;

  fetch("/lineup_shots", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ season, team, lineup })
  })
  .then(res => res.json())
 .then(shots => {
  console.log("Fetched shots:", shots);
  currentLineupShots = shots;
  currentPlayerFilter = null;


//   // Populate player dropdown
//   const select = document.getElementById("player-select");
//   const players = [...new Set(shots.map(d => d.PLAYER_NAME))].sort();
//   select.innerHTML = `<option value="">All Players</option>` + players.map(name => 
//     `<option value="${name}">${name}</option>`).join("");

const container = document.getElementById("assist-court-svg");
if (!container.querySelector("g.court-g")) {
  container.innerHTML = `
    <svg width="431" height="405.14" viewBox="0 0 431 405.14">
      ${courtSvgHtml}
    </svg>`;

  // defer execution to allow DOM paint cycle
  setTimeout(() => waitForCourtAndRender(currentLineupShots), 0);
} else {
waitForCourtAndRender(currentLineupShots, "#assist-court-svg", 10, "assist");
}

document.getElementById("assist-chart-controls").style.display = "block";

const heatToggle = document.getElementById("assist-heatmap-toggle");
const makesToggle = document.getElementById("assist-makes-only-toggle");

// Attach listeners only once
if (heatToggle && !heatToggle.dataset.bound) {
  heatToggle.addEventListener("change", () => renderShots(currentLineupShots, "#assist-court-svg", "assist"));
  heatToggle.dataset.bound = "true";
}
if (makesToggle && !makesToggle.dataset.bound) {
  makesToggle.addEventListener("change", () => renderShots(currentLineupShots, "#assist-court-svg", "assist"));
  makesToggle.dataset.bound = "true";
}

// Explicit render based on current toggle state
renderShots(currentLineupShots, "#assist-court-svg", "assist");

});
document.getElementById("reset-filter-button").onclick = () => {
  currentPlayerFilter = null;

  // Reset toggles
  const heatToggle = document.getElementById("assist-heatmap-toggle");
  const makesToggle = document.getElementById("assist-makes-only-toggle");
  if (heatToggle) heatToggle.checked = false;
  if (makesToggle) makesToggle.checked = false;

  // Redraw with full data
  renderShots(currentLineupShots, "#assist-court-svg", "assist");
};

}
function waitForCourtAndRender(shots, selector = "#assist-court-svg", maxTries = 10, togglePrefix = "assist") {
  let tries = 0;

  function tryRender() {
    const g = d3.select(selector).select("g.court-g");
    if (!g.empty()) {
      renderShots(shots, selector, togglePrefix);
    } else if (tries < maxTries) {
      tries++;
      setTimeout(tryRender, 30);
    } else {
      console.warn(`❌ Failed to find g.court-g in ${selector} after ${maxTries} tries`);
    }
  }

  tryRender();
}


async function fetchAndRenderTopLineups() {
  const team = document.getElementById("team")?.value;
  const season = document.getElementById("season")?.value;

  if (!team || !season) {
    console.error("❌ Missing team or season", { team, season });
    return;
  }

  console.log("📤 Sending POST to /get_top_lineups with:", { team, season });

  try {
    const res = await fetch("/get_top_lineups", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ team, season })
    });

    if (!res.ok) {
      throw new Error(`❌ Server error: ${res.status}`);
    }

    

    const result = await res.json();
    console.log("✅ Top lineups response:", result);

fillLineupTable(result); // use the fetched result
  } catch (error) {
    console.error("🔥 Error fetching top lineups:", error);
  }
}

const fillLineupTable = (lineups) => {
  const wrapper = document.getElementById("lineup-table-wrapper");
  const tbody = document.getElementById("lineup-table-body");
  
  // Hide the wrapper immediately
  if (wrapper) {
    wrapper.style.display = "none";
    wrapper.style.opacity = 0;
  }

  tbody.innerHTML = "";

  lineups.forEach((lineup) => {
    const row = document.createElement("tr");
    row.classList.add("lineup-row");
    row.dataset.lineup = lineup.id_key;

    const formattedLineupName = (lineup.GROUP_NAME || "").split("*--*").join(" - ");

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

    row.addEventListener("click", () => {
      document.querySelectorAll(".lineup-row").forEach(r => r.classList.remove("selected"));
      row.classList.add("selected");

      const lineupId = lineup.id_key;
      updateAssistNetwork(lineupId);
      updateLineupShotChart(lineupId);

      document.getElementById("assist-network-container").style.display = "block";
      document.getElementById("lineup-results").style.display = "flex";
      document.getElementById('assist-network-container')?.classList.add('show-network');
      document.getElementById('lineup-shot-chart-container')?.classList.add('show-network');
    });

    tbody.appendChild(row);
  });

if (wrapper) {
  wrapper.style.display = "block";  // make it visible
  requestAnimationFrame(() => {
    wrapper.style.opacity = 1;      // trigger CSS transition
  });
}
};



  // Lineup Assist Explorer
function updateLineupOptions(topLineups) {
  console.log("🧪 updateLineupOptions called with:", topLineups);

  if (!topLineups || !Array.isArray(topLineups)) {
    console.error("❌ Invalid topLineups data:", topLineups);
    return;
  }

  const container = document.getElementById("lineup-table");
  container.innerHTML = "";
  container.style.display = "block";

  const table = document.createElement("table");
  table.className = "lineup-table";

  topLineups.forEach((lineup, i) => {
    const row = document.createElement("tr");
    row.className = "lineup-row";
    row.dataset.lineup = lineup.id_key;

const cell = document.createElement("td");
cell.textContent = `${lineup.GROUP_NAME} (${lineup.MIN.toFixed(1)} min)`;
row.appendChild(cell); // ✅ YOU NEED THIS
table.appendChild(row); // ✅ Now the row has content
  });

  container.appendChild(table);

document.querySelectorAll(".lineup-row").forEach(row => {
  row.addEventListener("click", () => {
    document.querySelectorAll(".lineup-row").forEach(r => r.classList.remove("selected"));
    row.classList.add("selected");

    const lineup = row.dataset.lineup;
    console.log("Clicked lineup ID:", lineup);

    updateAssistNetwork(lineup);
    updateLineupShotChart(lineup);
    document.getElementById("assist-network-container").style.display = "block";
    document.getElementById("lineup-results").style.display = "flex";  // ✅ ADD THIS
  });
});
}
  const tabButtons = document.querySelectorAll(".tab-button");
  const lineupTab = document.getElementById("lineup-tab");
  const passingTab = document.getElementById("passing-tab");

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const tab = btn.dataset.tab;

      // Toggle visible tab
      if (tab === "lineup") {
        lineupTab.style.display = "block";
        passingTab.style.display = "none";
        document.body.classList.add("lineup-mode");
      } else {
        lineupTab.style.display = "none";
        passingTab.style.display = "block";
        document.body.classList.remove("lineup-mode");
      }

      // Active tab highlighting
      tabButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
    });
  });

  const activeTab = document.querySelector(".tab-button.active")?.dataset.tab;
if (activeTab === "assist") {
  const firstRow = document.querySelector(".lineup-row");
  if (firstRow) {
    updateAssistNetwork(firstRow.dataset.lineup);
    updateLineupShotChart(firstRow.dataset.lineup);
  }
} else {
  updatePassingNetwork();
}

  const seasonDropdown = document.getElementById("season");
 seasonDropdown.addEventListener("change", () => {
  console.log("🔥 Season change detected!");

  const selectedSeason = seasonDropdown.value;
  const team = document.getElementById("team")?.value;
  const activeTab = document.querySelector(".tab-button.active")?.dataset.tab;

  console.log("🌍 Selected team:", team);
  console.log("📅 Selected season:", selectedSeason);
  console.log("🧩 Active tab:", activeTab);

  if (!team) {
    console.warn("⚠️ No team selected");
    return;
  }

  if (activeTab === "lineup") {
    console.log("➡️ Fetching top lineups...");
    fetchAndRenderTopLineups(); // verify this is being called
  } else {
    console.log("➡️ Updating passing network...");
    updatePassingNetwork();
  }
});

});
