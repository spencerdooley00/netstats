// sharedShots.js

export function drawHeatmap(data, selector) {
  const g = d3.select(selector).select("g.court-g");
  if (g.empty()) return;

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

export function drawHexbins(data, selector) {
  const g = d3.select(selector).select("g.court-g");
  if (g.empty()) return;

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

export function drawCircles(data, selector) {
  const g = d3.select(selector).select("g.court-g");
  if (g.empty()) {
    console.warn(`❌ drawCircles aborted — ${selector} g.court-g not found`);
    return;
  }

  g.selectAll(".shot").remove();

  const tooltip = d3.select("body").append("div").attr("class", "tooltip").style("opacity", 0);

  g.selectAll("circle.shot")
    .data(data)
    .enter()
    .append("circle")
    .attr("class", "shot")
    .attr("cx", d => (d.LOC_X * 0.86) + 215.5)
    .attr("cy", d => (d.LOC_Y * 0.86) + 41.4)
    .attr("r", 4)
    .attr("fill", d => Number(d.SHOT_MADE_FLAG) === 1 ? "#f97316" : "#999")
    .attr("opacity", 0.65)
    .on("mouseover", function (event, d) {
      tooltip.transition().duration(200).style("opacity", 1);
      tooltip.html(`
        <strong>${d.PLAYER_NAME || ""}</strong><br/>
        <strong>Made:</strong> ${d.SHOT_MADE_FLAG == 1 ? "Yes" : "No"}
      `)
        .style("left", (event.pageX + 12) + "px")
        .style("top", (event.pageY - 28) + "px");
    })
    .on("mouseout", function () {
      tooltip.transition().duration(200).style("opacity", 0);
    });
}

export function renderShots(data, selector, togglePrefix = null) {
  const heatToggleId = togglePrefix ? `#${togglePrefix}-heatmap-toggle` : "#heatmap-toggle";
  const makesToggleId = togglePrefix ? `#${togglePrefix}-makes-only-toggle` : "#makes-only-toggle";

  const heat = document.querySelector(heatToggleId)?.checked;
  const makes = document.querySelector(makesToggleId)?.checked;

  let filtered = data;
  if (typeof currentPlayerFilter !== "undefined" && currentPlayerFilter) {
    filtered = filtered.filter(d =>
      d.PLAYER_NAME?.trim().toLowerCase() === currentPlayerFilter.trim().toLowerCase()
    );
  }
  if (makes) {
  filtered = filtered.filter(d => Number(d.SHOT_MADE_FLAG) === 1);
  }
console.log("heat:", heat, "makes:", makes, "filtered length:", filtered.length);
console.log("SHOT_MADE_FLAG values:", [...new Set(filtered.map(s => s.SHOT_MADE_FLAG))]);

  // heat ? drawHeatmap(filtered, selector) : drawHexbins(filtered, selector);
const modeButton = document.querySelector(
  togglePrefix
    ? `.chart-mode-toggle-${togglePrefix} .chart-mode-button.active`
    : `.chart-mode-toggle .chart-mode-button.active`
);
const mode = modeButton?.dataset.mode || "circle";
console.log("mode", mode)
if (mode === "heatmap") {
  drawHeatmap(filtered, selector);
} else if (mode === "hexbin") {
  drawHexbins(filtered, selector);
} else {
  drawCircles(filtered, selector);
}
}
// export function renderShots(data, selector, togglePrefix = null, playerName = null) {
//   const heatToggleId = togglePrefix ? `#${togglePrefix}-heatmap-toggle` : "#heatmap-toggle";
//   const makesToggleId = togglePrefix ? `#${togglePrefix}-makes-only-toggle` : "#makes-only-toggle";

//   const heat = document.querySelector(heatToggleId)?.checked;
//   const makes = document.querySelector(makesToggleId)?.checked;

//   let filtered = data;

//   if (playerName) {
//     filtered = filtered.filter(d => d.PLAYER_NAME?.trim().toLowerCase() === playerName.trim().toLowerCase());
//   }

//   if (makes) {
//     filtered = filtered.filter(d => Number(d.SHOT_MADE_FLAG) === 1);
//   }

//   heat ? drawHeatmap(filtered, selector) : drawHexbins(filtered, selector);
// }
