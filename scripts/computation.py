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

from collections import defaultdict

def compute_pass_degrees(edge_passes, players, threshold=6):
    pass_out = defaultdict(set)
    pass_in = defaultdict(set)

    for (sender, receiver), count in edge_passes.items():
        if count >= threshold:
            pass_out[sender].add(receiver)
            pass_in[receiver].add(sender)

    # Ensure all players have a degree entry (even if 0)
    pass_out_degree = {p: len(pass_out[p]) if p in pass_out else 0 for p in players}
    pass_in_degree = {p: len(pass_in[p]) if p in pass_in else 0 for p in players}

    return pass_out_degree, pass_in_degree


def compute_hub_score(p, percentiles):
    return (
        0.15 * percentiles["points"][p] +
        0.125 * percentiles["passes_made"][p] +
        0.125 * percentiles["passes_received"][p] +
        # 0.125 * (1 - abs(percentiles["pass_ratio"][p] - 1)) +  # balanced passing
        0.125 * percentiles["touches"][p] +
        # 0.10 * percentiles["pts_per_touch"][p] +
        0.10 * percentiles["time_of_possession"][p] +
        0.125 * percentiles['pass_out_degree'][p] +
        0.125 * percentiles['pass_in_degree'][p]
        # 0.05 * percentiles["fg_pct"][p] +
        # 0.05 * (percentiles["avg_drib_per_touch"][p]) 
        # 0.05 * (1 - percentiles["avg_sec_per_touch"][p])
    )

def compute_distributor_score(p, percentiles):
    return (
        0.25 * percentiles["passes_made"][p] +
        0.15 * (1 - percentiles["passes_received"][p]) +
        0.1 * (1 - percentiles["points"][p]) +
        # 0.15 * percentiles["touches"][p] +
        0.20 * percentiles["pass_ratio"][p] +  # skewed toward made passes
        # 0.05 * percentiles["time_of_possession"][p] +
        # 0.05 * percentiles["avg_drib_per_touch"][p]+
        0.15 * percentiles["pass_out_degree"][p] +
        0.15 * percentiles["pass_in_degree"][p]
    )

def compute_finisher_score(p, percentiles):
    return (
        0.30 * percentiles["points"][p] +
        0.25 * percentiles["passes_received"][p] +
        0.15 * (1 - percentiles["passes_made"][p]) +
        # 0.10 * percentiles["fg_pct"][p] +
        0.15 * percentiles["pass_in_degree"][p] +
        0.10 * percentiles["pts_per_touch"][p] +
        0.05 * percentiles["touches"][p] 
        # 0.05 * (1 / (percentiles["pass_ratio"][p] + 1e-5))  # or 1 - percentile(pass_ratio)
    )

def compute_black_hole_score(p, percentiles):
    return (
        0.30 * (percentiles["passes_received"][p] - percentiles["passes_made"][p]) +
        0.25 * (1 - percentiles["fg_pct"][p]) +
        0.15 * (1 - percentiles["pts_per_touch"][p]) +
        0.10 * percentiles["time_of_possession"][p] +
        0.10 * percentiles["avg_sec_per_touch"][p] +
        0.10 * percentiles["avg_drib_per_touch"][p]
    )


def compute_roles_by_percentile_scored(player_stats, edge_passes):
    # Filter for players with meaningful minutes
    filtered_stats = {
        p: s for p, s in player_stats.items()
        if s.get("games_played", 0) >= 10 and s.get("minutes_per_game", 0) >= 25
    }

    if not filtered_stats:
        return {
            "top_hubs": [], "distributors": [],
            "finishers": [], "strongest_connections": [],
            "black_holes": []
        }

    def percentile_dict(values_dict):
        names, values = zip(*values_dict.items())
        ranks = rankdata(values, method="average")
        return {name: (rank - 1) / (len(values) - 1) for name, rank in zip(names, ranks)}

    # Build base metrics
    def metric(name):
        return {p: s.get(name, 0.0) for p, s in filtered_stats.items()}

    points = metric("points")
    fg_pct = metric("fg_pct")
    touches = metric("touches")
    time_of_poss = metric("time_of_possession")
    pts_per_touch = metric("pts_per_touch")
    avg_sec_per_touch = metric("avg_sec_per_touch")
    avg_drib_per_touch = metric("avg_drib_per_touch")
    pmade = metric("passes_made")
    precv = metric("passes_received")

    # Compute pass ratio safely
    pass_ratio = {
        p: pmade[p] / (precv[p] + 1e-5)
        for p in filtered_stats
    }
    pass_out_degree, pass_in_degree = compute_pass_degrees(edge_passes, filtered_stats.keys(), threshold=8)

    # Compute percentiles
    percentiles = {
        "points": percentile_dict(points),
        "fg_pct": percentile_dict(fg_pct),
        "touches": percentile_dict(touches),
        "time_of_possession": percentile_dict(time_of_poss),
        "pts_per_touch": percentile_dict(pts_per_touch),
        "avg_sec_per_touch": percentile_dict(avg_sec_per_touch),
        "avg_drib_per_touch": percentile_dict(avg_drib_per_touch),
        "passes_made": percentile_dict(pmade),
        "passes_received": percentile_dict(precv),
        "pass_ratio": percentile_dict(pass_ratio),
        "pass_out_degree": percentile_dict(pass_out_degree),
        "pass_in_degree": percentile_dict(pass_in_degree)
    }

    # Compute role scores using helper functions
    hub_score = {p: compute_hub_score(p, percentiles) for p in filtered_stats}
    distributor_score = {p: compute_distributor_score(p, percentiles) for p in filtered_stats}
    finisher_score = {p: compute_finisher_score(p, percentiles) for p in filtered_stats}
    black_hole_score = {p: compute_black_hole_score(p, percentiles) for p in filtered_stats}

    # Top 400 or however many you want
    def top_n(score_dict, n=400):
        return sorted(score_dict.items(), key=lambda x: x[1], reverse=True)[:n]

    # Create player row with all scores
    def player_row(p):
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
            "hub_score": round(hub_score[p], 4),
            "distributor_score": round(distributor_score[p], 4),
            "finisher_score": round(finisher_score[p], 4),
            "black_hole_score": round(black_hole_score[p], 4)
        }

    # Strongest edges
    strongest_connections = sorted(edge_passes.items(), key=lambda x: x[1], reverse=True)[:25]

    return {
        "top_hubs": [player_row(p) for p, _ in top_n(hub_score)],
        "distributors": [player_row(p) for p, _ in top_n(distributor_score)],
        "finishers": [player_row(p) for p, _ in top_n(finisher_score)],
        "black_holes": [player_row(p) for p, _ in top_n(black_hole_score)],
        "strongest_connections": [
            {"from": f, "to": t, "passes": round(cnt, 2)}
            for (f, t), cnt in strongest_connections
        ]
    }

# def compute_roles_by_percentile_scored(player_stats, edge_passes):
#     # Filter for players with meaningful minutes
#     filtered_stats = {
#         p: s for p, s in player_stats.items()
#         if s.get("games_played", 0) >= 10 and s.get("minutes_per_game", 0) >= 25
#     }

#     if not filtered_stats:
#         return {
#             "top_hubs": [],
#             "distributors": [],
#             "finishers": [],
#             "strongest_connections": [],
#             "black_holes": []
#         }

#     def percentile_dict(values_dict):
#         names, values = zip(*values_dict.items())
#         ranks = rankdata(values, method="average")  # lower rank = lower value
#         percentiles = {name: (rank - 1) / (len(values) - 1) for name, rank in zip(names, ranks)}
#         return percentiles

#     # Build base metrics
#     points = {p: s["points"] for p, s in filtered_stats.items()}
#     pmade = {p: s["passes_made"] for p, s in filtered_stats.items()}
#     precv = {p: s["passes_received"] for p, s in filtered_stats.items()}
#     fg_pct = {p: s["fg_pct"] for p, s in filtered_stats.items()}

#     # Compute percentiles
#     points_pct = percentile_dict(points)
#     pmade_pct = percentile_dict(pmade)
#     precv_pct = percentile_dict(precv)

#     pass_balance = {
#         p: 1.0 - abs(pmade[p] - precv[p]) / (pmade[p] + precv[p] + 1e-5)
#         for p in filtered_stats
#     }

#     # Compute scores
#     hub_score = {
#         p: 0.3 * points_pct[p] + 0.3 * pmade_pct[p] + 0.3 * precv_pct[p] + 0.1 * pass_balance[p]
#         for p in filtered_stats
#     }

#     distributor_score = {
#         p: 0.5 * pmade_pct[p] + 0.3 * (1 - precv_pct[p]) + 0.2 * (1 - points_pct[p])
#         for p in filtered_stats
#     }

#     finisher_score = {
#         p: 0.4 * points_pct[p] + 0.4 * precv_pct[p] + 0.2 * (1 - pmade_pct[p])
#         for p in filtered_stats
#     }

#     black_hole_score = {
#         p: (precv_pct[p] - pmade_pct[p]) * (1 - fg_pct[p])
#         for p in filtered_stats
#     }

#     strongest_connections = sorted(edge_passes.items(), key=lambda x: x[1], reverse=True)[:25]

#     def top_n(score_dict, n=400):
#         return sorted(score_dict.items(), key=lambda x: x[1], reverse=True)[:n]

#     def player_row(p, score):
#         s = player_stats[p]
#         return {
#             "player": p,
#             "team": s["team"],
#             "points": round(s["points"], 1),
#             "fg_pct": round(s["fg_pct"], 3),
#             "passes_made": round(s["passes_made"], 2),
#             "passes_received": round(s["passes_received"], 2),
#             "minutes_per_game": round(s.get("minutes_per_game", 0.0), 1),
#             "games_played": int(s.get("games_played", 0)),
#             "hub_score": round(hub_score.get(p, 0.0), 4),
#             "distributor_score": round(distributor_score.get(p, 0.0), 4),
#             "finisher_score": round(finisher_score.get(p, 0.0), 4),
#             "black_hole_score": round(black_hole_score.get(p, 0.0), 4)
#         }


#     return {
#         "top_hubs": [player_row(p, hub_score) for p, hub_score in top_n(hub_score)],
#         "distributors": [player_row(p, distributor_score) for p, distributor_score in top_n(distributor_score)],
#         "finishers": [player_row(p, finisher_score) for p, finisher_score in top_n(finisher_score)],
#         "strongest_connections": [
#             {"from": f, "to": t, "passes": round(cnt, 2)}
#             for (f, t), cnt in strongest_connections
#         ],
#         "black_holes": [player_row(p, black_hole_score) for p, black_hole_score in top_n(black_hole_score)]
#     }

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
            touches = float(stats.get("TOUCHES", 0.0))
            time_of_possession = float(stats.get("TIME_OF_POSS", 0.0))
            team_abbrev = stats.get("TEAM_ABBREVIATION", team)
            pts_per_touch = float(stats.get("PTS_PER_TOUCH", 0.0))
            avg_sec_per_touch = float(stats.get("AVG_SEC_PER_TOUCH", 0.0))
            avg_drib_per_touch = float(stats.get("AVG_DRIB_PER_TOUCH", 0.0))
            
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
                "passes_received": 0.0 , # temporarily zero,
                "touches": touches,
                "time_of_possession": time_of_possession,
                "pts_per_touch": pts_per_touch,
                "avg_sec_per_touch": avg_sec_per_touch,
                "avg_drib_per_touch": avg_drib_per_touch,
                "minutes_per_game": player_minutes,
                "games_played": stats.get("GP", 0)
            }

    # assign received passes back into player_stats
    for player, received in passes_received_count.items():
        if player in player_stats:
            player_stats[player]["passes_received"] = received

    return compute_roles_by_percentile_scored(player_stats, edge_passes)

if __name__ == "__main__":
    all_season_roles = {}

    for season in SEASONS:
        print(f"🔍 Computing roles for {season}...")
        all_season_roles[season] = compute_roles_for_season(season)

    with open("league_roles_by_season.json", "w") as f:
        json.dump(all_season_roles, f, indent=2)

    print("✅ Saved to league_roles_by_season.json")
