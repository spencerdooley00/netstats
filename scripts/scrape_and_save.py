import json
import os
import time
from nba_api.stats.endpoints import TeamDashLineups, ShotChartLineupDetail
from nba_api.stats.static import teams, players
from dotenv import load_dotenv
import nba_on_court.nba_on_court.nba_on_court as noc
from scripts.passing_networks import all_stats  # required to resolve player IDs

load_dotenv()

headers = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'https://www.nba.com/'
}

OUTPUT_DIR = "network_data"
SEASONS = ["2014","2015","2016","2017","2018","2019","2020","2021","2022", "2023", "2024"]
ALL_STATS_PATH = "network_data/all_stats_test.json"
with open(ALL_STATS_PATH, "r") as f:
        all_stats = json.load(f)

def save_json(obj, filename):
    with open(os.path.join(OUTPUT_DIR, filename), "w") as f:
        json.dump(obj, f, indent=2)
def scrape_lineup_stats():
    existing_path = os.path.join(OUTPUT_DIR, "top_lineups.json")
    if os.path.exists(existing_path):
        with open(existing_path, "r") as f:
            all_lineups = json.load(f)
    else:
        all_lineups = {}

    for season in SEASONS:
        season_str = f"{season}-{int(season[2:])+1}"
        print(season_str)
        if season not in all_lineups:
            all_lineups[season] = {}

        for team in teams.get_teams():
            team_id = team["id"]
            team_abbr = team["abbreviation"]
            if team_abbr in all_lineups[season]:
                continue

            print(f"Scraping lineups for {team_abbr} ({season_str})...")
            try:
                df = TeamDashLineups(team_id=team_id, season=season_str, headers=headers).get_data_frames()[1]
            except Exception as e:
                print(f"Failed for {team_abbr}: {e}")
                continue

            df = df.sort_values("MIN", ascending=False).head(10)
            all_lineups[season][team_abbr] = []

            for _, row in df.iterrows():
                player_ids = row["GROUP_ID"].strip("-").split("-")
                lineup_entry = {
                    "ids": player_ids,
                    "group_name": row["GROUP_NAME"],
                    "stats": {k: row[k] for k in [
                        "GP", "MIN", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A",
                        "FG3_PCT", "OREB", "DREB", "REB", "AST", "TOV",
                        "STL", "BLK", "PTS", "PLUS_MINUS"
                    ]}
                }
                all_lineups[season][team_abbr].append(lineup_entry)
                time.sleep(0.6)

        # ✅ Save after each season
        save_json(all_lineups, "top_lineups.json")

    return all_lineups
def scrape_lineup_shots(all_lineups):
    path = os.path.join(OUTPUT_DIR, "lineup_shots.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            all_shots = json.load(f)
    else:
        all_shots = {}

    for season, teams_data in all_lineups.items():
        season_str = f"{season}-{int(season[2:])+1}"
        print(season_str)
        if season not in all_shots:
            all_shots[season] = {}

        for team, lineup_list in teams_data.items():
            if team not in all_shots[season]:
                all_shots[season][team] = {}

            for lineup in lineup_list:
                id_key = "-".join(lineup["ids"])
                if id_key in all_shots[season][team]:
                    continue

                print(f"Scraping shots for {season} {team} lineup {id_key}...")
                try:
                    df = ShotChartLineupDetail(
                        group_id=f"-{id_key}-",
                        context_measure_detailed="FGA",
                        season = season_str,
                        headers=headers
                        
                    ).get_data_frames()[0]
                    shots = df[["LOC_X", "LOC_Y", "SHOT_MADE_FLAG", "PLAYER_NAME"]].to_dict("records")
                    all_shots[season][team][id_key] = shots
                    time.sleep(0.6)
                except Exception as e:
                    print(f"Failed shot chart for {season} {team} {id_key}: {e}")

        # ✅ Save after each season
        save_json(all_shots, "lineup_shots.json")

import json
def get_player_shot_chart(player, team, season):
  season_stripped = int(season[:4])
  shot_data = noc.load_nba_data(seasons=season_stripped, data='shotdetail', in_memory=True, use_pandas=True)
  player_id = all_stats[season][team][player]['stats']['PLAYER_ID']
  player_shot_data = (
                      shot_data
                      .pipe(lambda df_: df_.loc[df_["PLAYER_ID"] == player_id])
                      .loc[:, ['LOC_X','LOC_Y', 'SHOT_MADE_FLAG']]
                      .reset_index(drop=True)
                     )
  return player_shot_data
def scrape_player_shots():
    path = os.path.join(OUTPUT_DIR, "player_shots.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            all_player_shots = json.load(f)
    else:
        all_player_shots = {}

    for season in SEASONS:
        season_str = f"{season}-{int(season[2:]) + 1}"
        
        print(season_str)
        if season_str not in all_stats:
            continue

        if season not in all_player_shots:
            all_player_shots[season] = {}

        for team, team_players in all_stats[season_str].items():
            if team not in all_player_shots[season]:
                all_player_shots[season][team] = {}

            for player in team_players:
                if player in all_player_shots[season][team]:
                    continue

                try:
                    df = get_player_shot_chart(player, team, season_str)
                    all_player_shots[season][team][player] = df.to_dict("records")
                    print(f"Added shots for {player} ({team}, {season})")
                except Exception as e:
                    print(f"❌ Skipping {player} ({team}, {season}): {e}")

        # ✅ Save after each season
        save_json(all_player_shots, "player_shots.json")

if __name__ == "__main__":
    # os.makedirs(OUTPUT_DIR, exist_ok=True)
    # lineup_data = scrape_lineup_stats()
    # scrape_lineup_shots(lineup_data)
    scrape_player_shots()
