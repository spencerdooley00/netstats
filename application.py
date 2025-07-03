
from flask import Flask, render_template, request, jsonify, abort, redirect, url_for, flash, session
import json
import markdown
import os
from scripts.passing_networks import fetch_data, create_network, generate_d3_data, get_player_shot_chart, calculate_network_metrics, get_default_starters

from functools import wraps
from dotenv import load_dotenv
load_dotenv()
import nba_api.stats.endpoints as nba
import nba_api.stats.static.teams as teams
import re
import boto3
import json
from flask import Flask

application = Flask(__name__)

@application.route("/")
def index():
    return "✅ NetStats deployed successfully!"
# application = Flask(__name__)
# s3 = boto3.client("s3")

# def load_json_from_s3(bucket, key):
#     try:
#         obj = s3.get_object(Bucket=bucket, Key=key)
#         return json.load(obj["Body"])
#     except Exception as e:
#         print(f"⚠️ Failed to load {key} from {bucket}: {e}")
#         return {}  # or None or [] depending on what your app expects

# # S3 Bucket
# bucket = "netstats-data"

# # Safely load all files
# all_stats = load_json_from_s3(bucket, "all_stats_test.json")
# lineup_shots_data = load_json_from_s3(bucket, "lineup_shots.json")
# top_lineups_data = load_json_from_s3(bucket, "top_lineups.json")
# player_shots_data = load_json_from_s3(bucket, "player_shots.json")
# assist_data = load_json_from_s3(bucket, "conditional_assist_networks_new_id.json")
# team_info = load_json_from_s3(bucket, "teams.json")

# # with open("network_data/lineup_shots.json", "r") as f:
# #     lineup_shots_data = json.load(f)

# # with open("network_data/player_shots.json", "r") as f:
# #     player_shots_data = json.load(f)
    

# # with open("network_data/conditional_assist_networks_new_id.json") as f:
# #     assist_data = json.load(f)

# # with open("network_data/all_stats_test.json") as f:
# #     all_stats = json.load(f)
    
    
# headers = {
#     'User-Agent': 'Mozilla/5.0',
#     'Referer': 'https://www.nba.com/'
# }

# POSTS_DIR = os.environ["POSTS_DIR"]
# application.secret_key = os.environ["SECRET_KEY"]

# USERNAME = os.environ["USERNAME"]
# PASSWORD = os.environ["PASSWORD"]

# @application.route("/")
# def home():
#     seasons = sorted(all_stats.keys(), reverse=True)
#     selected_season = seasons[0]
#     team_abbrs = [
#         "ATL", "BOS", "BKN", "CHA", "CHI", "CLE", "DAL", "DEN", "DET", "GSW",
#         "HOU", "IND", "LAC", "LAL", "MEM", "MIA", "MIL", "MIN", "NOP", "NYK",
#         "OKC", "ORL", "PHI", "PHX", "POR", "SAC", "SAS", "TOR", "UTA", "WAS"
#     ]
#     return render_template("home.html", season=selected_season, team_abbrs=team_abbrs)


# @application.route("/team/<team>")
# def team_view(team):
#     seasons = sorted(all_stats.keys(), reverse=True)
#     selected_season = request.args.get("season", seasons[0])
#     season_str = selected_season

#     # logo_map like { "LAL": 1610612747, ... }
#     logo_map = {
#         "ATL": 1610612737, "BOS": 1610612738, "BKN": 1610612751, "CHA": 1610612766,
#         "CHI": 1610612741, "CLE": 1610612739, "DAL": 1610612742, "DEN": 1610612743,
#         "DET": 1610612765, "GSW": 1610612744, "HOU": 1610612745, "IND": 1610612754,
#         "LAC": 1610612746, "LAL": 1610612747, "MEM": 1610612763, "MIA": 1610612748,
#         "MIL": 1610612749, "MIN": 1610612750, "NOP": 1610612740, "NYK": 1610612752,
#         "OKC": 1610612760, "ORL": 1610612753, "PHI": 1610612755, "PHX": 1610612756,
#         "POR": 1610612757, "SAC": 1610612758, "SAS": 1610612759, "TOR": 1610612761,
#         "UTA": 1610612762, "WAS": 1610612764
#     }

#     team_data = all_stats.get(season_str, {}).get(team, {})
#     if not team_data:
#         abort(404)

#     players = list(team_data.keys())
#     top_8 = sorted(players, key=lambda p: team_data[p]["stats"].get("MIN", 0), reverse=True)[:8]

#     return render_template(
#         "team.html",
#         team=team,
#         seasons=seasons,
#         selected_season=selected_season,
#         players=players,
#         selected_players=top_8,
#         logo_map=logo_map,
#         active_tab="passing"
#     )


# def login_required(f):
#     @wraps(f)
#     def wrapped(*args, **kwargs):
#         if not session.get("logged_in"):
#             flash("Please log in to access this page.")
#             return redirect(url_for("login"))
#         return f(*args, **kwargs)
#     return wrapped

# def get_posts():
#     posts = []
#     for filename in os.listdir(POSTS_DIR):
#         if filename.endswith(".md"):
#             slug = filename[:-3]
#             with open(os.path.join(POSTS_DIR, filename), "r", encoding="utf-8") as f:
#                 content = f.read()
#                 title = content.splitlines()[0].replace("# ", "").strip()
#                 excerpt = content.split("\n\n")[1][:200]  # first paragraph
#                 posts.append({
#                     "slug": slug,
#                     "title": title,
#                     "excerpt": excerpt + "...",
#                 })
#     return sorted(posts, key=lambda x: x["slug"], reverse=True)
# @application.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         if request.form["username"] == USERNAME and request.form["password"] == PASSWORD:
#             session["logged_in"] = True
#             flash("Logged in successfully!")
#             return redirect(url_for("blog_index"))
#         else:
#             flash("Incorrect username or password.")
#     return render_template("login.html")
# @application.route("/logout")
# def logout():
#     session.pop("logged_in", None)
#     flash("Logged out.")
#     return redirect(url_for("blog_index"))

# @application.route("/blog")
# def blog_index():
#     posts = get_posts()
#     return render_template("blog.html", posts=posts, logged_in=session.get("logged_in", False))

# @application.route("/blog/<slug>")
# def blog_post(slug):
#     path = os.path.join(POSTS_DIR, slug + ".md")
#     if not os.path.exists(path):
#         abort(404)
#     with open(path, "r", encoding="utf-8") as f:
#         content = f.read()
#         html = markdown.markdown(content)
#         title = content.splitlines()[0].replace("# ", "").strip()
#     return render_template("blog_post.html", title=title, content=html, slug=slug)


# @application.route("/blog/new", methods=["GET", "POST"])
# @login_required
# def new_post():
#     if request.method == "POST":
#         title = request.form["title"].strip()
#         content = request.form["content"].strip()
#         slug = title.lower().replace(" ", "-")

#         # Ensure slug is safe
#         filename = f"{slug}.md"
#         filepath = os.path.join(POSTS_DIR, filename)

#         # Prepend title as Markdown heading
#         full_content = f"# {title}\n\n{content}"

#         with open(filepath, "w", encoding="utf-8") as f:
#             f.write(full_content)

#         return redirect(url_for("blog_post", slug=slug))

#     return render_template("blog_new.html")

# @application.route("/blog/<slug>/delete", methods=["POST"])
# @login_required
# def delete_post(slug):
#     filepath = os.path.join(POSTS_DIR, slug + ".md")
#     if os.path.exists(filepath):
#         os.remove(filepath)
#         flash(f"Deleted post: {slug}")
#         return redirect(url_for("blog_index"))
#     else:
#         abort(404)
        
# # with open("network_data/all_stats_test.json", "r") as f:
# #     all_stats = json.load(f)

# # with open("teams.json", "r") as f:
# #     team_info = json.load(f)

# @application.route("/get_lineups", methods=["POST"])
# def get_lineups():
#     data = request.get_json()
#     season = data["season"]
#     team = data["team"]

#     lineups = list(assist_data[season][team].keys())
#     return jsonify({"lineups": lineups})

# from nba_api.stats.static import players
# def extract_player_id_or_name(token):
#     # Case: literal ID inside brackets like [1630173]
#     if re.fullmatch(r"\[\d+\]", token):
#         return token.strip("[]")
#     return token  # normal name

# def sanitize_key(key):
#     return re.sub(r"[.$#[\]/']", '', key)

# @application.route("/update_assist_network", methods=["POST"])
# def update_assist_network():
#     data = request.get_json()
#     season = data["season"]
#     team = data["team"]
#     raw_lineup = data["lineup"]
#     season_short = season[:4]


#     # ✅ STEP 1: Convert full-name lineup to player ID key if needed
#     if "-" in raw_lineup and all(part.isdigit() for part in raw_lineup.split("-")):
#         id_key = raw_lineup
#     else:
#         player_ids = []
#         for token in raw_lineup:
#             val = extract_player_id_or_name(token)
#             if val.isdigit():
#                 player_ids.append(val)
#             else:
#                 matches = players.find_players_by_full_name(val)
#                 if matches:
#                     player_ids.append(str(matches[0]["id"]))
#                 else:
#                     return jsonify({"error": f"Could not find player ID for '{token}'"}), 400
#         id_key = "-".join(player_ids)
#     # lineup_shots = nba.ShotChartLineupDetail(group_id="-"+id_key+"-", context_measure_detailed="FGA", headers=headers).get_data_frames()[0]
#     # ✅ STEP 2: Get assist data
#     try:
#         assist_dict = assist_data[season_short][team][id_key]
#     except KeyError:
#         return jsonify({"error": f"Lineup not found: {id_key}"}), 404

#     all_player_ids = set([pid for pid in assist_dict] +
#                          [tid for v in assist_dict.values() for tid in v])

#     # ✅ STEP 3: ID → Name
#     id_to_name = {}
#     for pid in all_player_ids:
#         try:
#             id_to_name[pid] = players.find_player_by_id(int(pid))["full_name"]
#         except:
#             id_to_name[pid] = f"Unknown ({pid})"

#     # ✅ STEP 4: Image lookup using sanitized full names
#     stats_team = all_stats.get(season, {}).get(team, {})
#     img_lookup = {
#         pid: stats_team.get(sanitize_key(name), {}).get("img", "")
#         for pid, name in id_to_name.items()
#     }

#     # ✅ STEP 5: Build D3 graph
#     nodes, links, seen = [], [], set()
#     for source_id, targets in assist_dict.items():
#         source_name = id_to_name.get(source_id, f"Unknown ({source_id})")
#         if source_name not in seen:
#             nodes.append({
#                 "id": source_name,
#                 "name": source_name,
#                 "img": img_lookup.get(source_id, "")
#             })
#             seen.add(source_name)

#         for target_id, weight in targets.items():
#             target_name = id_to_name.get(target_id, f"Unknown ({target_id})")
#             if target_name not in seen:
#                 nodes.append({
#                     "id": target_name,
#                     "name": target_name,
#                     "img": img_lookup.get(target_id, "")
#                 })
#                 seen.add(target_name)

#             links.append({
#                 "source": source_name,
#                 "target": target_name,
#                 "weight": weight
#             })

#     return jsonify({"nodes": nodes, "links": links})

# @application.route("/update_network", methods=["POST"])
# def update_network():
#     data = request.get_json()
#     season = data.get("season")
#     team = data.get("team")
#     selected_players = data.get("players", [])

#     if season and team:
#         all_data, team_data, team_info = fetch_data(season, team)
#         color = team_info["primary_color"]

#         # Get all players sorted by MIN descending
#         sorted_players = sorted(
#             team_data.items(),
#             key=lambda item: item[1]["stats"].get("MIN", 0),
#             reverse=True
#         )
#         top8_players = [player for player, _ in sorted_players[:8]]

#         # If user did not select players, default to top 8
#         if not selected_players:
#             selected_players = top8_players

#         _, G = create_network(team_data, team, color, "Pass Per Game", selected_players)
#         d3_data = generate_d3_data(G)

#         return jsonify({
#             "nodes": d3_data["nodes"],
#             "links": d3_data["links"],
#             "players": [p for p, _ in sorted_players],
#             "selected": selected_players
#         })

#     return jsonify({"nodes": [], "links": [], "players": [], "selected": []})

# @application.route("/player_shots", methods=["POST"])
# def player_shots():
#     data = request.get_json()
#     player = data.get('player')
#     team = data.get('team')
#     season = data.get('season')
#     season = season[:4]
#     shots = player_shots_data.get(season, {}).get(team, {}).get(player, [])
#     return jsonify(shots)


# @application.route("/blog")
# def blog():
#     return render_template("blog.html")


# @application.route("/get_top_lineups", methods=["POST"])
# def get_top_lineups():
#     data = request.get_json()
#     # team_id = data["team_id"]
#     season = data["season"]
#     team = data['team']
#     # team = teams.find_team_name_by_id(team_id)['abbreviation']

#     season_str = season[:4]

#     # Load data from JSON
#     lineups = top_lineups_data.get(season_str, {}).get(team, [])
#     team_stats = all_stats.get(season_str, {}).get(team, {})
#     # Build PLAYER_ID → full name map from all_stats
#     player_lookup = {
#         str(player_data["stats"]["PLAYER_ID"]): name
#         for name, player_data in team_stats.items()
#         if "PLAYER_ID" in player_data["stats"]
#     }

#     rows = []
#     for lineup in lineups:
#         raw_ids = lineup["ids"]
#         full_names = [player_lookup.get(pid, f"[{pid}]") for pid in raw_ids]
#         full_names = [name.replace("]", "") for name in full_names]
#         full_names = [
#             players.find_player_by_id(name.replace("[", "")).get("full_name", name) if "[" in name else name
#             for name in full_names
#         ]

#         full_lineup_key = "*--*".join(full_names)
#         stats = {
#             "GROUP_NAME": full_lineup_key,
#             "id_key": raw_ids,  # <-- ADD THIS LINE
#             **lineup["stats"]
#         }

#         rows.applicationend(stats)

#     return jsonify(rows)




# @application.route("/lineup_shots", methods=["POST"])
# def lineup_shots():
#     data = request.get_json()
#     season = data["season"]
#     team = data["team"]
#     lineup = data["lineup"]
#     season = season[:4]
    
#     try:
#         ids = lineup
#         id_key = "-".join(str(pid) for pid in ids)
#         shots = lineup_shots_data.get(season, {}).get(team, {}).get(id_key, [])
#         return jsonify(shots)
#     except Exception as e:
#         return jsonify([])



# def get_lineup_ids(season, team, lineup):
#     """
#     Given a season, team, and lineup name, return a list of player IDs in order.
#     """
#     # Convert "2024" → "2024-25"
#     season_str = f"{season}-{int(season[2:]) + 1}"


#     player_names = lineup.split("*--*")  # assume lineup names are hyphen-delimited
#     player_names = [name.strip() for name in player_names]
#     team_data = all_stats.get(season_str, {}).get(team, {})
#     ids = []
#     for name in player_names:
#         name = sanitize_key(name)
        
#         player_data = team_data.get(name)
#         # if player_data and "id" in player_data:
#         ids.applicationend(player_data['stats']["PLAYER_ID"])
#         # else:
#         #     raise ValueError(f"Player ID not found for {name} in {season_str} {team}")

#     return ids


# @application.route("/test_metrics")
# def test_metrics():
#     season = "2024-25"
#     team = "BOS"
#     edge_info = "Pass Per Game"  # or "Assists"
#     color = "gray"  # optional edge color

#     # Get default starter list
#     selected_players = get_default_starters(season, team)

#     # Load raw data
#     _, team_data, _ = fetch_data(season, team)

#     # Create NetworkX graph
#     _, G = create_network(team_data, team, color, edge_info, selected_players)

#     # Build scoring lookup from stats
#     scoring_lookup = {
#         player: team_data[player]["stats"].get("PTS", 0)
#         for player in selected_players
#     }

#     # Calculate metrics
#     metrics = calculate_network_metrics(G, scoring_lookup)

#     # Print to console for dev
#     import pprint
#     pprint.pprint(metrics)

#     return jsonify(metrics)  # View in browser as JSON
