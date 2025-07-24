---
title: "How We Built NetStats"
date: "2025-07-23"
description: "A technical deep dive into building the NBA's cleanest passing network visualization."
slug: "how-we-built-netstats"
image_url: "/static/article_thumbs/netstats-preview-final.jpg"
---

# How We Built NetStats

NetStats started with a simple idea: **pass tracking should be beautiful**.

As fans and analysts, we often focus on assists — but what about **all the other passes** that shape the flow of a game? NetStats sets out to visualize **every pass between players** over a full season, and reveal the hidden architecture of team offense.

---

## The Stack

To make this happen, we built a stack that’s fast, flexible, and scalable:

- 🐍 **Python** for data scraping, processing, and backend
- 🔥 **D3.js** for interactive player networks and shot charts
- ☁️ **AWS (S3 + DynamoDB)** for static data storage and lightning-fast lookups
- 🧪 **NBA Stats API** for official play-by-play, lineup, and player data

We started by scraping **player-level passing data** using the `nba_api` Python package. We structured each season into nested JSON files grouped by team and player.

---

## From Data to Network

The heart of NetStats is the **passing network**.

We built each network using:

- **Nodes** for players
- **Edges** weighted by pass frequency
- **Tooltips** showing stats like touches, assists, and FG%

Using **NetworkX** and custom logic, we transform raw passing counts into a D3-friendly force-directed graph. The final visualization is:
- Fully interactive
- Styled by team
- Toggled by player selection or flow mode

---

## Shot Charts and Lineup Explorer

Beyond networks, we wanted to let users **see the results** of ball movement.

Each player and lineup includes:

- A **shot chart** (hexbin, heatmap, or dot mode)
- A **lineup explorer** showing assist-only networks within 5-man groups
- Filterable toggles and real-time interactivity

This lets users explore both **intent** (passes) and **outcome** (shots).

---

## What’s Next?

We’re continuing to evolve NetStats with:

- Player role analysis (hub, finisher, distributor)
- Searchable player explorer
- League-wide trends and historical comparisons

Want to dive deeper or explore your favorite team? Head to [NetStats.dev](https://www.netstats.dev) and explore.

Or hit us up with feedback — this is just the beginning.
