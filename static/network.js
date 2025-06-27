// Fetch and render the network
fetch("/static/network.json")
    .then(response => response.json())
    .then(data => renderNetwork(data));

function renderNetwork(data) {
    const width = 900;
    const height = 700;

    // Clear previous graph
    d3.select("#network").html("");

    const svg = d3.select("#network")
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    svg.append("defs").append("marker")
        .attr("id", "arrow")
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 20)  // Adjust based on node size
        .attr("refY", 0)
        .attr("markerWidth", 4)
        .attr("markerHeight", 4)
        .attr("refX", 12) // adjust so arrows sit nicely at node edges
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M0,-5L10,0L0,5")
        .attr("fill", "#999");

    const simulation = d3.forceSimulation(data.nodes)
        .force("link", d3.forceLink(data.links).id(d => d.id).distance(350))  // longer edges
        .force("charge", d3.forceManyBody().strength(-700))  // more repulsion
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collision", d3.forceCollide().radius(40))


;

    // const link = svg.append("g")
    //     .attr("stroke", "#aaa")
    //     .selectAll("line")
    //     .data(data.links)
    //     .join("line")
    //     .attr("stroke-width", d => Math.max(1, d.weight * 1));  // Adjust scale factor as needed
    const link = svg.append("g")
        .selectAll("path")
        .data(data.links)
        .enter().append("path")
        .attr("stroke", "#999")
        // .attr("stroke-width", d => Math.max(1, d.weight * 0.5))  // Adjust scale factor as needed
        // .style("stroke-width", d => Math.min(Math.sqrt(d.weight) * 2,6))
        .style("stroke-width", d => Math.sqrt(d.weight) * 2)
        .attr("fill", "none")
        .attr("marker-end", "url(#arrow)");
    
    const node = svg.append("g")
        .selectAll("image")
        .data(data.nodes)
        .join("image")
        .attr("xlink:href", d => d.img)
        .attr("width", 80)
        .attr("height", 80)
        .attr("x", -20)
        .attr("y", -20)
        .call(drag(simulation));

    node.append("title")
        .text(d => d.id);

    simulation.on("tick", () => {
            link.attr("d", d => {
                const dx = d.target.x - d.source.x;
                const dy = d.target.y - d.source.y;
                const dr = Math.sqrt(dx * dx + dy * dy) * 2.5;
                return `M${d.source.x},${d.source.y}A${dr},${dr} 0 0,1 ${d.target.x},${d.target.y}`;
            });
        
            node
                .attr("transform", d => `translate(${d.x},${d.y})`);
        });

}

// Dragging behavior
function drag(simulation) {
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    return d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);
}
