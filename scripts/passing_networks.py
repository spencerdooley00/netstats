import json
import networkx as nx
from pyvis.network import Network
from nltk import ngrams
import nba_on_court.nba_on_court.nba_on_court as noc
import boto3
import json

s3 = boto3.client("s3")

def load_json_from_s3(bucket, key):
    obj = s3.get_object(Bucket=bucket, Key=key)
    return json.load(obj["Body"])

team_info_all = load_json_from_s3("netstats-data", "teams.json")

all_stats = load_json_from_s3("netstats-data", "all_stats_test.json")
# lineup_shots_data = load_json_from_s3("netstats-data", "lineup_shots.json")
# top_lineups_data = load_json_from_s3("netstats-data", "top_lineups.json")
# player_shots_data = load_json_from_s3("netstats-data", "player_shots.json")
# assist_data = load_json_from_s3("netstats-data", "conditional_assist_networks_new_id.json")
# Helper function: Jaccard similarity for name matching


def jaccard_similarity(s1, s2):
    set1 = set(ngrams(s1, 3))
    set2 = set(ngrams(s2, 3))
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union)


def check_name_in_list(given_name, player_names, threshold=0.6):
    for name in player_names:
        similarity = jaccard_similarity(given_name.lower(), name.lower())
        if similarity >= threshold:
            return True
    return False

# Fetch data from loaded JSON


def fetch_data(season, team):
    season_data = all_stats[season]
    team_data = season_data[team]
    team_info = team_info_all[f"Season={season}"][team]
    return season_data, team_data, team_info

# Create the network graph


def create_network(team_data, team_name, color, edge_info, selected_players):
    net = Network('600px', '800px', bgcolor='#FFFFFF',
                  font_color='black', directed=True)
    G = nx.DiGraph()

    selected_players = [
        player for player in selected_players if player in team_data.keys()]
    for player in selected_players:
        player_dict = team_data[player]
        net.add_node(player, shape="image",
                     image=player_dict["img"], size=50, label=' ')
        G.add_node(player, image = player_dict["img"], stats = player_dict['stats'])

    for player in selected_players:
        if "passes" in team_data[player]:
            player_passing = team_data[player]["passes"]
            for player_passed_to, player_dict in player_passing.items():
                if player_passed_to in selected_players:
                    w = player_dict["passes"] if edge_info == "Pass Per Game" else player_dict.get(
                        "ast", 0)
                    net.add_edge(player, player_passed_to,
                                 value=w, title=str(w), color=color)
                    G.add_edge(player, player_passed_to, weight=w)
    net.set_options("""
    const options = {
      "nodes": {
        "borderWidth": 0,
        "borderWidthSelected": 7,
        "opacity": 1,
        "font": {
          "size": 36
        },
        "scaling": {
          "max": 46
        },
        "size": 19
      },
      "edges": {
        "color": {
          "inherit": true,
          "opacity": 0.5
        },
        "selfReferenceSize": 1,
        "selfReference": {
          "angle": 0.7853981633974483
        },
        "smooth": {
          "forceDirection": "none"
        }
      },
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -326,
          "springLength": 70,
          "damping": 1
        },
        "minVelocity": 0.75,
        "solver": "forceAtlas2Based",
        "timestep": 0.25
      }
    }
    """)
    custom_style = """
                    <style>
                      body { margin: 0; }
                      #mynetwork {
                        border: none !important;
                        box-shadow: none !important;
                        padding: 0 !important;
                        background: white !important;
                      }
                    </style>
                    """
    net.html += custom_style
    # Save network as an HTML file
    # net.save_graph(f"static/{team_name}_network.html")
    return net, G

# Generate default starter list


def get_default_starters(season, team):
    return team_info_all[f"Season={season}"][team]["starter_info"]["starters"]

def generate_d3_data(G):
    def format_name_for_url(name):
        # Example: "LeBron James" → "lebron_james"
        return name.lower().replace(" ", "_")

    nodes = []
    for node in G.nodes():
        name = G.nodes[node].get("name", node)
        # player_image = f"https://cdn.nba.com/headshots/nba/latest/260x190/{node}.png"  # or custom logic
        player_image = G.nodes[node].get("image", node)
        player_stats = G.nodes[node].get("stats", node)
        nodes.append({
            "id": node,
            "name": name,
            "img": player_image,
            "stats": player_stats
        })

    links = [{"source": u, "target": v, "weight": G[u][v].get("weight", 1)} for u, v in G.edges()]
    return {"nodes": nodes, "links": links}
  
def get_player_shot_chart(player, team, season):
  season_stripped = int(season[:4])
  shot_data = noc.load_nba_data(seasons=season_stripped, data='shotdetail', in_memory=True, use_pandas=True)
  # season = f"{season}-{int(str(season)[2:])+1}"
  player_id = all_stats[season][team][player]['stats']['PLAYER_ID']
  print(player_id)
  # player_id = all_stats[]
  player_shot_data = (
                      shot_data
                      .pipe(lambda df_: df_.loc[df_["PLAYER_ID"] == player_id])
                      .loc[:, ['LOC_X','LOC_Y', 'SHOT_MADE_FLAG']]
                      .reset_index(drop=True)
                     )
  return player_shot_data

def calculate_network_metrics(G, scoring_lookup=None):
    """
    Calculates centrality and role metrics for each node in the graph.
    
    Parameters:
        G (nx.DiGraph): Directed graph of the passing network
        scoring_lookup (dict): Optional dict mapping player names to point totals

    Returns:
        dict: Dictionary of metrics per player
    """
    metrics = {}
    scoring_lookup = scoring_lookup or {}

    in_deg = dict(G.in_degree(weight='weight'))
    out_deg = dict(G.out_degree(weight='weight'))
    in_conn = dict(G.in_degree())
    out_conn = dict(G.out_degree())
    deg_cent = nx.degree_centrality(G)
    bet_cent = nx.betweenness_centrality(G, weight='weight', normalized=True)
    close_cent = nx.closeness_centrality(G)
    eigen_cent = nx.eigenvector_centrality_numpy(G, weight='weight')

    for node in G.nodes():
        in_weight = in_deg.get(node, 0)
        out_weight = out_deg.get(node, 0)
        score = scoring_lookup.get(node, 0)

        metrics[node] = {
            "in_weight": in_weight,
            "out_weight": out_weight,
            "in_degree": in_conn.get(node, 0),
            "out_degree": out_conn.get(node, 0),
            "degree_centrality": deg_cent.get(node, 0),
            "betweenness": bet_cent.get(node, 0),
            "closeness": close_cent.get(node, 0),
            "eigenvector": eigen_cent.get(node, 0),
            "score": score,
            "hub_score": in_weight + out_weight + score,
            "distributor_index": in_conn.get(node, 0) + out_conn.get(node, 0) + in_weight + out_weight,
            "feeder_index": out_weight - in_weight,
            "finisher_index": in_weight - out_weight + score,
        }

    return metrics
