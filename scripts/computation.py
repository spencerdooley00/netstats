import json
from collections import defaultdict
from dynamo_cache import get_all_stats
# add all seasons 
TEAMS = [
    "ATL", "BOS", "BKN", "CHA", "CHI", "CLE", "DAL", "DEN", "DET",
    "GSW", "HOU", "IND", "LAC", "LAL", "MEM", "MIA", "MIL", "MIN",
    "NOP", "NYK", "OKC", "ORL", "PHI", "PHX", "POR", "SAC", "SAS",
    "TOR", "UTA", "WAS"
]
SEASONS = [f"{year}-{str(year+1)[-2:]}" for year in range(2014, 2025)]
import numpy as np
import numpy as np
from scipy.stats import rankdata

def compute_roles_by_percentile_scored(player_stats, edge_passes):
    # Filter for players with meaningful minutes
    filtered_stats = {
        p: s for p, s in player_stats.items()
        if s.get("games_played", 0) >= 10 and s.get("minutes_per_game", 0) >= 25
    }

    if not filtered_stats:
        return {
            "top_hubs": [],
            "distributors": [],
            "finishers": [],
            "strongest_connections": [],
            "black_holes": []
        }

    def percentile_dict(values_dict):
        names, values = zip(*values_dict.items())
        ranks = rankdata(values, method="average")  # lower rank = lower value
        percentiles = {name: (rank - 1) / (len(values) - 1) for name, rank in zip(names, ranks)}
        return percentiles

    # Build base metrics
    points = {p: s["points"] for p, s in filtered_stats.items()}
    pmade = {p: s["passes_made"] for p, s in filtered_stats.items()}
    precv = {p: s["passes_received"] for p, s in filtered_stats.items()}
    fg_pct = {p: s["fg_pct"] for p, s in filtered_stats.items()}

    # Compute percentiles
    points_pct = percentile_dict(points)
    pmade_pct = percentile_dict(pmade)
    precv_pct = percentile_dict(precv)

    pass_balance = {
        p: 1.0 - abs(pmade[p] - precv[p]) / (pmade[p] + precv[p] + 1e-5)
        for p in filtered_stats
    }

    # Compute scores
    hub_score = {
        p: 0.3 * points_pct[p] + 0.3 * pmade_pct[p] + 0.3 * precv_pct[p] + 0.1 * pass_balance[p]
        for p in filtered_stats
    }

    distributor_score = {
        p: 0.5 * pmade_pct[p] + 0.3 * (1 - precv_pct[p]) + 0.2 * (1 - points_pct[p])
        for p in filtered_stats
    }

    finisher_score = {
        p: 0.4 * points_pct[p] + 0.4 * precv_pct[p] + 0.2 * (1 - pmade_pct[p])
        for p in filtered_stats
    }

    black_hole_score = {
        p: (precv_pct[p] - pmade_pct[p]) * (1 - fg_pct[p])
        for p in filtered_stats
    }

    strongest_connections = sorted(edge_passes.items(), key=lambda x: x[1], reverse=True)[:25]

    def top_n(score_dict, n=20):
        return sorted(score_dict.items(), key=lambda x: x[1], reverse=True)[:n]

    def player_row(p, score):
        s = player_stats[p]
        return {
            "player": p,
            "team": s["team"],
            "points": round(s["points"], 1),
            "fg_pct": round(s["fg_pct"], 3),
            "passes_made": round(s["passes_made"], 2),
            "passes_received": round(s["passes_received"], 2),
            "minutes_per_game": round(s.get("minutes_per_game", 0.0), 1),
            "games_played": int(s.get("games_played", 0)),
            "score": round(score, 4)
        }


    return {
        "top_hubs": [player_row(p, score) for p, score in top_n(hub_score)],
        "distributors": [player_row(p, score) for p, score in top_n(distributor_score)],
        "finishers": [player_row(p, score) for p, score in top_n(finisher_score)],
        "strongest_connections": [
            {"from": f, "to": t, "passes": round(cnt, 2)}
            for (f, t), cnt in strongest_connections
        ],
        "black_holes": [player_row(p, score) for p, score in top_n(black_hole_score)]
    }

def compute_roles_by_percentile(player_stats, edge_passes, minutes_threshold=25.0):
    # Filter by minutes
    # print(player_stats)
    filtered_stats = {
        p: s for p, s in player_stats.items()
        if s.get("minutes", 0) >= minutes_threshold
    }
    print(filtered_stats)

    if not filtered_stats:
        return {
            "top_hubs": [],
            "distributors": [],
            "finishers": [],
            "strongest_connections": [],
            "black_holes": []
        }

    # Percentile thresholds
    points = np.array([s["points"] for s in filtered_stats.values()])
    passes_made = np.array([s["passes_made"] for s in filtered_stats.values()])
    passes_received = np.array([s["passes_received"] for s in filtered_stats.values()])

    p_thresh = np.percentile(points, 85)
    pm_thresh = np.percentile(passes_made, 85)
    pr_thresh = np.percentile(passes_received, 85)
    pm_low = np.percentile(passes_made, 50)
    pr_low = np.percentile(passes_received, 50)
    pt_low = np.percentile(points, 50)

    def player_row(p):
        s = player_stats[p]
        return {
            "player": p,
            "team": s["team"],
            "points": round(s["points"], 1),
            "fg_pct": round(s["fg_pct"], 3),
            "passes_made": round(s["passes_made"], 2),
            "passes_received": round(s["passes_received"], 2)
        }

    # Roles
    top_hubs = [
        p for p, s in filtered_stats.items()
        if s["points"] >= p_thresh and
           s["passes_made"] >= pm_thresh and
           s["passes_received"] >= pr_thresh and
           abs(s["passes_made"] - s["passes_received"]) < 0.25 * max(s["passes_made"], s["passes_received"])
    ]

    distributors = [
        p for p, s in filtered_stats.items()
        if s["passes_made"] >= pm_thresh and
           s["passes_received"] < pr_low and
           s["points"] < pt_low
    ]

    finishers = [
        p for p, s in filtered_stats.items()
        if s["passes_received"] >= pr_thresh and
           s["passes_made"] < pm_low and
           s["points"] >= p_thresh
    ]

    # Strongest connections
    strongest_connections = sorted(edge_passes.items(), key=lambda x: x[1], reverse=True)[:25]

    # Black holes
    black_holes = sorted({
        p: (s["passes_received"] - s["passes_made"]) * (1 - s["fg_pct"])
        for p, s in filtered_stats.items()
    }.items(), key=lambda x: x[1], reverse=True)[:25]

    return {
        "top_hubs": [player_row(p) for p in top_hubs],
        "distributors": [player_row(p) for p in distributors],
        "finishers": [player_row(p) for p in finishers],
        "strongest_connections": [
            {"from": f, "to": t, "passes": round(cnt, 2)}
            for (f, t), cnt in strongest_connections
        ],
        "black_holes": [player_row(p) for p, _ in black_holes]
    }
def compute_roles_for_season(season):
    player_stats = {}
    passes_received_count = defaultdict(float)
    edge_passes = defaultdict(float)

    for team in TEAMS:
        players = get_all_stats(season, team)
        if not players:
            continue

        for player, data in players.items():
            stats = data.get("stats", {})
            points = float(stats.get("PTS", 0.0))
            fg_pct = float(stats.get("FG_PCT", 0.0))
            team_abbrev = stats.get("TEAM_ABBREVIATION", team)

            # passes_made = sum of passes to teammates
            player_passes = data.get("passes", {})
            passes_made = sum(float(p.get("passes", 0)) for p in player_passes.values())
            player_minutes = float(stats.get("MIN", 0.0))

            # accumulate received passes per target player
            for teammate, p in player_passes.items():
                passes_received_count[teammate] += float(p.get("passes", 0))
                edge_passes[(player, teammate)] += float(p.get("passes", 0))

            player_stats[player] = {
                "team": team_abbrev,
                "points": points,
                "fg_pct": fg_pct,
                "passes_made": passes_made,
                "passes_received": 0.0 , # temporarily zero
                "minutes_per_game": player_minutes,
                "games_played": stats.get("GP", 0)
            }

    # assign received passes back into player_stats
    for player, received in passes_received_count.items():
        if player in player_stats:
            player_stats[player]["passes_received"] = received

    return compute_roles_by_percentile_scored(player_stats, edge_passes)

def compute_roles(player_stats, edge_passes):
    def top_k(d, k=25, sort_key=None):
        return sorted(d.items(), key=sort_key, reverse=True)[:k]

    # ---- WEIGHTED SCORES ----
    top_hubs = top_k({
        p: (
            0.4 * s["points"] +
            0.3 * s["passes_made"] +
            0.3 * s["passes_received"] -
            0.2 * abs(s["passes_made"] - s["passes_received"])
        )
        for p, s in player_stats.items()
    }, sort_key=lambda x: x[1])

    distributors = top_k({
        p: (
            1.0 * s["passes_made"] -
            0.6 * s["passes_received"] -
            0.3 * s["points"]
        )
        for p, s in player_stats.items()
    }, sort_key=lambda x: x[1])

    finishers = top_k({
        p: (
            0.6 * s["points"] +
            0.6 * s["passes_received"] -
            0.4 * s["passes_made"]
        )
        for p, s in player_stats.items()
    }, sort_key=lambda x: x[1])

    strongest_connections = top_k(edge_passes, sort_key=lambda x: x[1])

    black_holes = top_k({
        p: (s["passes_received"] - s["passes_made"]) * (1 - s["fg_pct"])
        for p, s in player_stats.items()
    }, sort_key=lambda x: x[1])

    def player_row(p):
        s = player_stats[p]
        return {
            "player": p,
            "team": s["team"],
            "points": round(s["points"], 1),
            "fg_pct": round(s["fg_pct"], 3),
            "passes_made": round(s["passes_made"], 2),
            "passes_received": round(s["passes_received"], 2)
        }

    return {
        "top_hubs": [player_row(p) for p, _ in top_hubs],
        "distributors": [player_row(p) for p, _ in distributors],
        "finishers": [player_row(p) for p, _ in finishers],
        "strongest_connections": [
            {"from": f, "to": t, "passes": round(count, 2)}
            for (f, t), count in strongest_connections
        ],
        "black_holes": [player_row(p) for p, _ in black_holes]
    }


if __name__ == "__main__":
    all_season_roles = {}

    for season in SEASONS:
        print(f"🔍 Computing roles for {season}...")
        all_season_roles[season] = compute_roles_for_season(season)

    with open("league_roles_by_season.json", "w") as f:
        json.dump(all_season_roles, f, indent=2)

    print("✅ Saved to league_roles_by_season.json")
