---
title: "How We Built NetStats"
date: "2025-07-23"
description: "A technical deep dive into building the NBA's cleanest passing network visualization."
slug: "how-we-built-netstats"
image_url: "/static/article_thumbs/netstats-preview-final.jpg"
---

## Why Netstats


## Netstats Overview

The heart of NetStats is the **passing network**.

Each network consists of:

- **Nodes** for players which have **attributes** holding the player's statistics
- **Edges (weighted)** representing pass frequency and are directional from the passing player to the recieving player


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
