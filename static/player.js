import { courtSvgHtml } from './courtSvg.js';  // if applicable
import { renderShots } from './sharedShots.js';  // optional if you abstract shot logic

document.addEventListener("DOMContentLoaded", () => {
  const player = document.getElementById("player-name")?.textContent.trim();
  const team = document.getElementById("team")?.textContent.trim();
  const season = document.getElementById("season")?.textContent.trim();

  const rawEdges = JSON.parse(document.getElementById("player-edges-data").textContent);
  const rawNodes = JSON.parse(document.getElementById("player-nodes-data").textContent);

  // Normalize edges and nodes
  function clean(str) {
    return str.normalize("NFKD").replace(/[\u0300-\u036f]/g, "").trim();
  }

  const links = rawEdges.map(d => ({
    source: clean(d.from),
    target: clean(d.to),
    passes: d.passes
  }));

  const nodes = rawNodes.map(d => ({
    ...d,
    id: clean(d.id)
  }));

  renderPlayerNetwork(nodes, links, player);
  fetchAndRenderShotChart(player, team, season);
});

function renderPlayerNetwork(nodes, links, player) {
const width = 600, height = 600;  // match the card height

const svg = d3.select("#player-network")
  .append("svg")
  .attr("width", "100%")
  .attr("height", "100%")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("preserveAspectRatio", "xMidYMid meet");
  const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id).distance(220))
    .force("charge", d3.forceManyBody().strength(-300))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide(60))  // Prevent overlapping
  const link = svg.append("g")
    .selectAll("path")
    .data(links)
    .join("path")
    .attr("fill", "none")
    .attr("stroke", "#aaa")
    .attr("stroke-width", d => Math.max(2, d.passes ** 0.75));

  const node = svg.append("g")
    .selectAll("image")
    .data(nodes)
    .join("image")
    .attr("xlink:href", d => d.image)
    .attr("width", 80)
    .attr("height", 80)
    .attr("x", d => d.x - 40)
    .attr("y", d => d.y - 40)
    .attr("clip-path", "circle(40px)")
    .attr("cursor", "pointer");

  const label = svg.append("g")
    .selectAll("text")
    .data(nodes)
    .join("text")
    .text(d => d.id)
    .attr("dy", 15)
    .attr("fill", "#fff")
    .attr("font-size", "12px")
    .attr("text-anchor", "middle");

  simulation.on("tick", () => {
    link.attr("d", d => {
      const dx = d.target.x - d.source.x;
      const dy = d.target.y - d.source.y;
      const dr = Math.sqrt(dx * dx + dy * dy);
      return `M${d.source.x},${d.source.y} A${dr},${dr} 0 0,1 ${d.target.x},${d.target.y}`;
    });

    node.attr("x", d => d.x - 40).attr("y", d => d.y - 40);
    label.attr("x", d => d.x).attr("y", d => d.y + 30);
  });
    // ✅ Call radar chart

  if (window.roleStats) {
    drawRadarChart(window.roleStats, false);  // default = raw

const normalizeToggle = document.getElementById("normalize-toggle");
if (normalizeToggle) {
  normalizeToggle.addEventListener("change", () => {
    drawRadarChart(window.roleStats, normalizeToggle.checked);
  });
}
  }
}

function fetchAndRenderShotChart(player, team, season) {
  const courtSvg = d3.select("#court-svg");
  courtSvg.html(courtSvgHtml);

  fetch("/player_shots", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ player, season, team })
  })
    .then(res => res.json())
    .then(data => {
      window.shots = data;
      renderShots(data, "#court-svg");
    })
    .catch(err => {
      console.error("Failed to fetch shot chart:", err);
    });



    
}
let radarChartInstance = null;

function drawRadarChart(roleStats, normalize = false) {
  const ctx = document.getElementById('roleRadarChart');
  if (!ctx) return;

  const categories = ['hub', 'finisher', 'distributor', 'black_hole'];
  const labels = ['Hub', 'Finisher', 'Distributor', 'Black Hole'];

  const data = categories.map(role => {
    const playerVal = roleStats.player?.[role] || 0;
    const leagueAvg = roleStats.league?.[role] || 1;
    return normalize ? playerVal / leagueAvg : playerVal;
  });

  // Destroy previous chart if it exists
  if (radarChartInstance) {
    radarChartInstance.destroy();
  }

  radarChartInstance = new Chart(ctx, {
    type: 'radar',
    data: {
      labels,
      datasets: [{
        label: normalize ? 'Relative to League Avg' : 'Raw Score',
        data,
        backgroundColor: 'rgba(93, 173, 226, 0.2)',
        borderColor: 'rgba(93, 173, 226, 1)',
        pointBackgroundColor: 'rgba(93, 173, 226, 1)',
        borderWidth: 2
      }]
    },
    options: {
      scales: {
        r: {
          suggestedMin: 0,
          suggestedMax: normalize ? 2 : 1,
          ticks: {
            stepSize: normalize ? 0.5 : 0.2,
            backdropColor: 'transparent',
            color: '#aaa'
          },
          pointLabels: {
            color: 'white',
            font: { size: 14 }
          },
          grid: { color: '#444' },
          angleLines: { color: '#555' }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}




