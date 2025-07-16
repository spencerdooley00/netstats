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
  const width = 600, height = 600;
  const svg = d3.select("#player-network")
    .append("svg")
    .attr("width", width)
    .attr("height", height);

  const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id).distance(220))
    .force("charge", d3.forceManyBody().strength(-300))
    .force("center", d3.forceCenter(width / 2, height / 2));

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
