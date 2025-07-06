
from nba_api.stats.static import players
import decimal
from scripts.dynamo_cache import (
    get_all_stats,
    get_player_shots,
    get_lineup_shots,
    get_top_lineups,
    get_assist_data
)
from flask import Flask, jsonify, request
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from flask import Flask
import boto3
import re
import nba_api.stats.static.teams as teams
import nba_api.stats.endpoints as nba
from flask import Flask, render_template, request, jsonify, abort, redirect, url_for, flash, session
import json
import markdown
import os
from scripts.passing_networks import fetch_data, create_network, generate_d3_data, get_player_shot_chart, calculate_network_metrics, get_default_starters

from functools import wraps
from dotenv import load_dotenv
load_dotenv()


# DynamoDB client + resource
REGION = "us-east-2"
dynamodb = boto3.resource("dynamodb", region_name=REGION)
application = Flask(__name__)

s3 = boto3.client("s3")
bucket = "netstats-data"

REGION = "us-east-2"
dynamodb = boto3.resource("dynamodb", region_name=REGION)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super().default(obj)


@application.route("/")
def home():

    seasons = ["2024-25", "2023-24", "2022-23", "2021-22", "2020-21", "2019-20", "2018-19", "2017-18", "2016-17", "2015-16", "2014-15"]
    selected_season = seasons[0]

    team_abbrs = [
        "ATL", "BOS", "BKN", "CHA", "CHI", "CLE", "DAL", "DEN", "DET", "GSW",
        "HOU", "IND", "LAC", "LAL", "MEM", "MIA", "MIL", "MIN", "NOP", "NYK",
        "OKC", "ORL", "PHI", "PHX", "POR", "SAC", "SAS", "TOR", "UTA", "WAS"
    ]
    return render_template("home.html", season=selected_season, team_abbrs=team_abbrs)


@application.route("/team/<team>")
@application.route("/team/<team>")
def team_view(team):
    # Manually define available seasons
    seasons = ["2024-25", "2023-24", "2022-23", "2021-22", "2020-21", "2019-20", "2018-19", "2017-18", "2016-17", "2015-16", "2014-15"]

    # Get selected season from query parameter, fallback to latest
    selected_season = request.args.get("season", seasons[0])
    # season_str is just the short year string used in your Dynamo keys
    season_str = selected_season  # keep this short form for use in Dynamo

    team_data = get_all_stats(season_str, team)

    logo_map = {
        "ATL": 1610612737, "BOS": 1610612738, "BKN": 1610612751, "CHA": 1610612766,
        "CHI": 1610612741, "CLE": 1610612739, "DAL": 1610612742, "DEN": 1610612743,
        "DET": 1610612765, "GSW": 1610612744, "HOU": 1610612745, "IND": 1610612754,
        "LAC": 1610612746, "LAL": 1610612747, "MEM": 1610612763, "MIA": 1610612748,
        "MIL": 1610612749, "MIN": 1610612750, "NOP": 1610612740, "NYK": 1610612752,
        "OKC": 1610612760, "ORL": 1610612753, "PHI": 1610612755, "PHX": 1610612756,
        "POR": 1610612757, "SAC": 1610612758, "SAS": 1610612759, "TOR": 1610612761,
        "UTA": 1610612762, "WAS": 1610612764
    }

    if not team_data:
        abort(404)

    players = list(team_data.keys())
    top_8 = sorted(players, key=lambda p: team_data[p]["stats"].get(
        "MIN", 0), reverse=True)[:8]

    return render_template(
        "team.html",
        team=team,
        seasons=seasons,
        selected_season=selected_season,
        players=players,
        selected_players=top_8,
        logo_map=logo_map,
        active_tab="passing"
    )


def extract_player_id_or_name(token):
    # Case: literal ID inside brackets like [1630173]
    if re.fullmatch(r"\[\d+\]", token):
        return token.strip("[]")
    return token  # normal name


def sanitize_key(key):
    return re.sub(r"[.$#[\]/']", '', key)

@application.route("/update_assist_network", methods=["POST"])
def update_assist_network():
    data = request.get_json()
    season = data["season"]          # "2024-25"
    team = data["team"]
    raw_lineup = data["lineup"]
    season_short = season[:4]        # "2024"

    from scripts.dynamo_cache import get_all_stats, get_assist_data

    # ✅ STEP 1: Convert full-name lineup to player ID key if needed
    if "-" in raw_lineup and all(part.isdigit() for part in raw_lineup.split("-")):
        id_key = raw_lineup
    else:
        player_ids = []
        for token in raw_lineup:
            val = extract_player_id_or_name(token)
            if val.isdigit():
                player_ids.append(val)
            else:
                matches = players.find_players_by_full_name(val)
                if matches:
                    player_ids.append(str(matches[0]["id"]))
                else:
                    return jsonify({"error": f"Could not find player ID for '{token}'"}), 400
        id_key = "-".join(player_ids)

    # ✅ STEP 2: Get assist data directly from DynamoDB
    assist_dict = get_assist_data(season_short, team, id_key)
    if not assist_dict:
        return jsonify({"error": f"Lineup not found: {id_key}"}), 404

    # ✅ STEP 3: Get all_stats directly from DynamoDB
    stats_team = get_all_stats(season, team)

    # ✅ STEP 4: Build ID → name map
    all_player_ids = set([pid for pid in assist_dict] +
                         [tid for v in assist_dict.values() for tid in v])

    id_to_name = {}
    for pid in all_player_ids:
        try:
            id_to_name[pid] = players.find_player_by_id(int(pid))["full_name"]
        except:
            id_to_name[pid] = f"Unknown ({pid})"

    # ✅ STEP 5: Build image lookup
    img_lookup = {
        pid: stats_team.get(sanitize_key(name), {}).get("img", "")
        for pid, name in id_to_name.items()
    }

    # ✅ STEP 6: Build D3-style nodes + links
    nodes, links, seen = [], [], set()
    for source_id, targets in assist_dict.items():
        source_name = id_to_name.get(source_id, f"Unknown ({source_id})")
        if source_name not in seen:
            nodes.append({
                "id": source_name,
                "name": source_name,
                "img": img_lookup.get(source_id, "")
            })
            seen.add(source_name)

        for target_id, weight in targets.items():
            target_name = id_to_name.get(target_id, f"Unknown ({target_id})")
            if target_name not in seen:
                nodes.append({
                    "id": target_name,
                    "name": target_name,
                    "img": img_lookup.get(target_id, "")
                })
                seen.add(target_name)

            links.append({
                "source": source_name,
                "target": target_name,
                "weight": weight
            })

    return jsonify({"nodes": nodes, "links": links})


@application.route("/update_network", methods=["POST"])
def update_network():
    from scripts.dynamo_cache import get_all_stats

    data = request.get_json()
    season = data.get("season")        # e.g., "2024-25"
    team = data.get("team")
    selected_players = data.get("players", [])

    if season and team:
        # 🟢 Direct DynamoDB lookup
        team_data = get_all_stats(season, team)

        # 🟡 Define static color info
        team_colors = {
            "ATL": "#E03A3E", "BOS": "#007A33", "BKN": "#000000", "CHA": "#1D1160",
            "CHI": "#CE1141", "CLE": "#860038", "DAL": "#00538C", "DEN": "#0E2240",
            "DET": "#C8102E", "GSW": "#1D428A", "HOU": "#CE1141", "IND": "#002D62",
            "LAC": "#C8102E", "LAL": "#552583", "MEM": "#5D76A9", "MIA": "#98002E",
            "MIL": "#00471B", "MIN": "#0C2340", "NOP": "#0C2340", "NYK": "#006BB6",
            "OKC": "#007AC1", "ORL": "#0077C0", "PHI": "#006BB6", "PHX": "#1D1160",
            "POR": "#E03A3E", "SAC": "#5A2D81", "SAS": "#C4CED4", "TOR": "#CE1141",
            "UTA": "#002B5C", "WAS": "#002B5C"
        }
        color = team_colors.get(team, "#999")

        # 🔵 Sort players by minutes
        sorted_players = sorted(
            team_data.items(),
            key=lambda item: item[1]["stats"].get("MIN", 0),
            reverse=True
        )
        top8_players = [player for player, _ in sorted_players[:8]]

        if not selected_players:
            selected_players = top8_players

        # 🟣 Build passing network
        _, G = create_network(team_data, team, color,
                              "Pass Per Game", selected_players)
        d3_data = generate_d3_data(G)

        return jsonify({
            "nodes": d3_data["nodes"],
            "links": d3_data["links"],
            "players": [p for p, _ in sorted_players],
            "selected": selected_players
        })

    return jsonify({"nodes": [], "links": [], "players": [], "selected": []})


@application.route("/player_shots", methods=["POST"])
def player_shots():

    def convert_decimals(obj):
        if isinstance(obj, list):
            return [convert_decimals(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        else:
            return obj

    data = request.get_json()
    player = data.get('player')
    team = data.get('team')
    season = data.get('season')
    season = season[:4]  # Ensure format like "2024"

    shots = get_player_shots(season, team, player)
    shots_clean = convert_decimals(shots)
    return jsonify(shots_clean)


@application.route("/blog")
def blog():
    return render_template("blog.html")


def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj
@application.route("/get_top_lineups", methods=["POST"])
def get_top_lineups_route():
    data = request.get_json()
    season = data["season"][:4]
    team = data["team"]

    # Query new format
    all_items = get_top_lineups(season, team)  # returns list with one item that contains "lineups"
    team_stats = get_all_stats(season, team)

    # PLAYER_ID → full name
    player_lookup = {
        str(player_data["stats"].get("PLAYER_ID")): name
        for name, player_data in team_stats.items()
        if "PLAYER_ID" in player_data.get("stats", {})
    }

    rows = []
    for item in all_items:
        for lineup in item.get("lineups", []):
            raw_ids = lineup["ids"]
            full_names = [player_lookup.get(pid, f"[{pid}]") for pid in raw_ids]
            full_names = [name.replace("]", "") for name in full_names]
            full_names = [
                players.find_player_by_id(name.replace("[", "")).get("full_name", name)
                if "[" in name else name
                for name in full_names
            ]
            full_lineup_key = "*--*".join(full_names)

            stats = {
                "GROUP_NAME": full_lineup_key,
                "id_key": raw_ids,
                **lineup["stats"]
            }
            rows.append(stats)

    return jsonify(convert_decimals(rows))


@application.route("/lineup_shots", methods=["POST"])
def lineup_shots():
    data = request.get_json()
    season = data["season"][:4]
    team = data["team"]
    lineup_ids = data["lineup"]  # this should be a list like ["1628384", "1630173", ...]

    try:
        id_key = "-".join(str(pid) for pid in lineup_ids)
        shots = get_lineup_shots(season, team, id_key)
        return jsonify(shots)
    except Exception as e:
        print("Error loading lineup shots:", e)
        return jsonify([])

def get_lineup_ids(season, team, lineup):
    """
    Given a season, team, and lineup name, return a list of player IDs in order.
    """
    season_str = f"{season}-{int(season[2:]) + 1}"  # "2024" → "2024-25"
    team_data = get_all_stats(season[:4], team)

    player_names = lineup.split("*--*")
    ids = []
    for name in player_names:
        name = sanitize_key(name)
        player_data = team_data.get(name)
        if player_data and "stats" in player_data and "PLAYER_ID" in player_data["stats"]:
            ids.append(str(player_data["stats"]["PLAYER_ID"]))
        else:
            raise ValueError(f"Missing ID for {name} in {season_str} {team}")
    return ids

@application.route("/test_metrics")
def test_metrics():
    season = "2024-25"
    team = "BOS"
    edge_info = "Pass Per Game"  # or "Assists"
    color = "gray"  # optional edge color

    # Get default starter list
    selected_players = get_default_starters(season, team)

    # Load raw data
    _, team_data, _ = fetch_data(season, team)

    # Create NetworkX graph
    _, G = create_network(team_data, team, color, edge_info, selected_players)

    # Build scoring lookup from stats
    scoring_lookup = {
        player: team_data[player]["stats"].get("PTS", 0)
        for player in selected_players
    }

    # Calculate metrics
    metrics = calculate_network_metrics(G, scoring_lookup)

    # Print to console for dev
    import pprint
    pprint.pprint(metrics)

    return jsonify(metrics)  # View in browser as JSON
