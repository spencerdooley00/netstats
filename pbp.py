import pandas as pd
import numpy as np
from collections import defaultdict
from nba_api.stats.endpoints import playbyplayv2
import nba_on_court as noc
import time
import json
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import re
import asyncio
import nest_asyncio
import nba_on_court.nba_on_court.nba_on_court as noc

# Initialize nested asyncio to allow nested event loops
nest_asyncio.apply()

# Initialize Firebase with your credentials
# cred = credentials.Certificate(
#     "nba-networks-firebase-adminsdk-twpxv-ef05487a05.json")
# default_app = firebase_admin.initialize_app(cred, {
#     'databaseURL': "https://nba-networks-default-rtdb.firebaseio.com/"
# })


def load_play_by_play_data(year):
    """
    Load play-by-play data from a CSV file.
    """
    
    return noc.load_nba_data(seasons=year, data='nbastats', in_memory=True, use_pandas=True)

# pd.read_csv(f"data/play-by-play/nbastats_{year}.csv")


def fetch_game_ids(play_by_play_data):
    """
    Extract unique game IDs from play-by-play data.
    """
    return pd.unique(play_by_play_data["GAME_ID"])


def sanitize_key(key):
    """
    Sanitize a string to remove Firebase forbidden characters.
    """
    return re.sub(r'[.$#[\]/]', '', key)


def get_play_by_play(game_id):
    """
    Fetch play-by-play data for a given game ID from NBA API.
    """
    game_id = f"00{game_id}"
    try:
        return playbyplayv2.PlayByPlayV2(game_id=game_id).play_by_play.get_data_frame()
    except:
        time.sleep(30)
        try:
            return playbyplayv2.PlayByPlayV2(game_id=game_id).play_by_play.get_data_frame()
        except json.decoder.JSONDecodeError:
            return None


def extract_team_info(play_by_play_data):
    """
    Extract home and away team information from play-by-play data.
    """
    if not play_by_play_data.empty:
        all_teams = [team for team in pd.unique(
            play_by_play_data.loc[:, 'PLAYER1_TEAM_ABBREVIATION']) if team is not None]
        return all_teams[0], all_teams[1]
    return None, None


def filter_assist_data(all_games_combined):
    """
    Filter and transform play-by-play data to extract assist events.
    """
    ast_df = (
        all_games_combined
        .loc[
            (all_games_combined.EVENTMSGTYPE == 1) &
            (~all_games_combined.PLAYER2_ID.isna()) &
            (all_games_combined.PLAYER2_ID != 0)
        ]
        .rename(columns={'PLAYER1_ID': 'SHOT_PLAYER', 'PLAYER2_ID': 'AST_PLAYER'})
        .reset_index(drop=True)
    )

    cols = [
        'SHOT_PLAYER', 'AST_PLAYER', 'HOME_PLAYER1', 'HOME_PLAYER2',
        'HOME_PLAYER3', 'HOME_PLAYER4', 'HOME_PLAYER5',
        'AWAY_PLAYER1', 'AWAY_PLAYER2', 'AWAY_PLAYER3',
        'AWAY_PLAYER4', 'AWAY_PLAYER5'
    ]

    ast_df = ast_df[['HOMEDESCRIPTION', 'VISITORDESCRIPTION',
                     'PLAYER1_TEAM_ABBREVIATION', 'PLAYER2_TEAM_ABBREVIATION'] + cols]
    ast_df[cols] = ast_df[cols].apply(noc.players_name, result_type="expand")

    return ast_df


def add_other_players(ast_df):
    """
    Add columns for other players on the court during assist events.
    """
    cols = ['HOME_PLAYER1', 'HOME_PLAYER2', 'HOME_PLAYER3', 'HOME_PLAYER4', 'HOME_PLAYER5',
            'AWAY_PLAYER1', 'AWAY_PLAYER2', 'AWAY_PLAYER3', 'AWAY_PLAYER4', 'AWAY_PLAYER5']

    for i in range(1, 6):
        ast_df[f'OTHER_PLAYER{i}'] = np.where(
            ~ast_df['HOMEDESCRIPTION'].isna(
            ), ast_df[f'HOME_PLAYER{i}'], ast_df[f'AWAY_PLAYER{i}']
        )
    ast_df["TEAM"] = ast_df["PLAYER1_TEAM_ABBREVIATION"]
    return ast_df.dropna(subset=[f'OTHER_PLAYER{i}' for i in range(1, 6)], how='all').reset_index(drop=True)


def create_assist_dict(filtered_ast_df, year):
    """
    Create a nested dictionary to store assist statistics organized by year, team, lineup, and players.
    """
    assist_dict = defaultdict(lambda: defaultdict(
        lambda: defaultdict(lambda: defaultdict(int))))

    for _, row in filtered_ast_df.iterrows():
        lineup = sorted([row[f'OTHER_PLAYER{i}'] for i in range(1, 6)])
        lineup_str = sanitize_key('-'.join(lineup))
        assist_player = sanitize_key(row['AST_PLAYER'])
        shot_player = sanitize_key(row['SHOT_PLAYER'])
        team = row['TEAM']

        if year not in assist_dict:
            assist_dict[year] = defaultdict(
                lambda: defaultdict(lambda: defaultdict(int)))
        if team not in assist_dict[year]:
            assist_dict[year][team] = defaultdict(lambda: defaultdict(int))
        if lineup_str not in assist_dict[year][team]:
            assist_dict[year][team][lineup_str] = defaultdict(int)
        if assist_player not in assist_dict[year][team][lineup_str]:
            assist_dict[year][team][lineup_str][assist_player] = defaultdict(
                int)

        assist_dict[year][team][lineup_str][assist_player][shot_player] += 1

    return convert_to_dict(assist_dict)


def convert_to_dict(d):
    if isinstance(d, defaultdict):
        d = {k: convert_to_dict(v) for k, v in d.items()}
    elif isinstance(d, dict):
        d = {k: convert_to_dict(v) for k, v in d.items()}
    return d


def merge_assist_data(existing_data, new_data):
    """
    Merge new assist data into existing data structure.
    """
    for year, year_data in new_data.items():
        if year not in existing_data:
            existing_data[year] = year_data
        else:
            for team, team_data in year_data.items():
                if team not in existing_data[year]:
                    existing_data[year][team] = team_data
                else:
                    for lineup, lineup_data in team_data.items():
                        if lineup not in existing_data[year][team]:
                            existing_data[year][team][lineup] = lineup_data
                        else:
                            for assist_player, assist_player_data in lineup_data.items():
                                if assist_player not in existing_data[year][team][lineup]:
                                    existing_data[year][team][lineup][assist_player] = assist_player_data
                                else:
                                    for shot_player, count in assist_player_data.items():
                                        if shot_player not in existing_data[year][team][lineup][assist_player]:
                                            existing_data[year][team][lineup][assist_player][shot_player] = count
                                        else:
                                            existing_data[year][team][lineup][assist_player][shot_player] += count
    return existing_data


def clear_processed_games(year):
    """
    Clear the processed games tracker for a given year in Firebase.
    """
    db_ref = db.reference(f"processed_games/{year}")
    db_ref.delete()
    print(f"Cleared processed games tracker for year {year}.")


# def clear_conditional_assists(year):
#     """
#     Clear the conditional assists data in Firebase.
#     """
#     db_ref = db.reference(f"conditional_assist_networks/{year}")
#     db_ref.delete()
#     print("Cleared conditional assist networks in Firebase.")


# async def write_to_firebase_async(data, year):
#     """
#     Write data to Firebase asynchronously.
#     """
#     loop = asyncio.get_event_loop()
#     ref = db.reference(f"conditional_assist_networks/{year}")
#     await loop.run_in_executor(None, ref.update, data)
#     print(f"Data pushed to Firebase for year {year}.")
def write_to_json_async(data, year, output_dir="output"):
    """
    Write data to a JSON file asynchronously.
    """

    os.makedirs(output_dir, exist_ok=True)
    
    file_path = os.path.join(output_dir, f"conditional_assist_networks.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Data written to {file_path}.")

# async def write_game_ids_to_firebase_async(game_ids, year, game_data):
#     """
#     Write game IDs to Firebase asynchronously along with team information.
#     """
#     loop = asyncio.get_event_loop()
#     ref = db.reference(f"processed_games/{year}")
#     data = {sanitize_key(f"00{game_id}")            : game_data[game_id] for game_id in game_ids}
#     await loop.run_in_executor(None, ref.update, data)
#     print(f"Game IDs and team info pushed to Firebase for year {year}.")


def is_game_processed(game_id, year):
    """
    Check if the game ID has already been processed.
    """
    sanitized_game_id = f"00{game_id}"
    # db_ref = db.reference(f"processed_games/{year}/{sanitized_game_id}")
    # return db_ref.get() is not None


def process_play_by_play_async(game_ids, year, pbp_data):
    all_games_data = []
    assist_data = {}
    # assist_data = defaultdict(lambda: defaultdict(
    #     lambda: defaultdict(lambda: defaultdict(int))))
    processed_game_ids = []
    game_data = {}
    print(pbp_data['GAME_ID'].unique())
    # print(len(game_ids))
    for idx, game_id in enumerate(game_ids):
        # if is_game_processed(game_id, year):
        #     continue

        try:
                # pbp = get_play_by_play(game_id)
            pbp = pbp_data[pbp_data['GAME_ID']==game_id].reset_index()
            # print(game_id, pbp.head())
            # print(game_id, pbp.head())
            # if pbp is not None:
            try:
                pbp_with_players = noc.players_on_court(pbp)
            except IndexError:
                continue
            # print(pbp_with_players.head())
            home_team, away_team = extract_team_info(pbp_with_players)
            game_data[game_id] = {
                "home_team": home_team,
                "away_team": away_team,
                "processed": True
            }
            all_games_data.append(pbp_with_players)
            # print(len(all_games_data))
            processed_game_ids.append(game_id)
            # print(len(all_games_data))
            # else:
            #     continue
        except KeyError:
            # print("here")
            # time.sleep(5)
            continue
        
        # time.sleep(5)

    print(f"Processed game {game_id} for year {year}.")

    if (idx + 1) % 10 == 0 or (idx + 1) == len(game_ids):
        print(len(all_games_data))
        all_games_combined = pd.concat(all_games_data, ignore_index=True)
        filtered_ast_df = filter_assist_data(all_games_combined)
        filtered_ast_df = add_other_players(filtered_ast_df)
        current_assist_data = create_assist_dict(filtered_ast_df, year)

        # with open(file_path, "w", encoding="utf-8") as f:
        #     existing_assist_data = json.load(f, ensure_ascii=False, indent=2)

        # assist_data = merge_assist_data(existing_assist_data, assist_data_dict)
        # write_to_json_async(assist_data[year], year)
        # await write_game_ids_to_firebase_async(processed_game_ids, year, game_data)
        print(
            f"Data for {len(processed_game_ids)} games pushed to Firebase for year {year}.")
        all_games_data = []
        processed_game_ids = []

    print(f"Finished processing all games for year {year}.")
    # print(assist_data)
    assist_data_dict = {}
    file_path = os.path.join("output", f"conditional_assist_networks.json")

    with open(file_path, "r") as f:
        existing_assist_data = json.load(f)
    existing_assist_data[year] = current_assist_data
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(existing_assist_data, f, ensure_ascii=False, indent=2)
    

    # return assist_data


# def count_processed_game_ids(year):
    # db_ref = db.reference(f"processed_games/{year}")
    # processed_games = db_ref.get()
    # if processed_games:
    #     num_games_processed = len(processed_games)
    #     print(
    #         f"Number of processed game IDs for year {year}: {num_games_processed}")
    # else:
    #     print(f"No processed game IDs found for year {year}.")


def main():
    years = [2014, 2015, 2016, 2017, 2018, 2019,
             2020, 2021, 2022, 2023, 2024][::-1]  # 2023
    for year in years:
        file_path = os.path.join("output", "conditional_assist_networks.json")

        with open(file_path, "r") as f:
            d = json.load(f)
        # existing_assist_data[year] = current_assist_data
        # clear_conditional_assists(year)
        # clear_processed_games(year)
        # count_processed_game_ids(year)
        pbp_data = load_play_by_play_data(year)
        print(pbp_data.shape)
        season_games = fetch_game_ids(pbp_data)
        print(len(season_games))
        # del pbp_data
        process_play_by_play_async(season_games, year, pbp_data)
        # print(f"Processed data for year {year}: {assist_data}")

if __name__ == "__main__":
    main()


# import pandas as pd
# import numpy as np
# from collections import defaultdict
# from nba_api.stats.endpoints import playbyplayv2
# import nba_on_court as noc
# import time
# import json
# import os
# import firebase_admin
# from firebase_admin import credentials
# from firebase_admin import db
# import re
# import asyncio
# import nest_asyncio

# # Initialize nested asyncio to allow nested event loops
# nest_asyncio.apply()

# # Initialize Firebase with your credentials
# cred = credentials.Certificate("nba-networks-firebase-adminsdk-twpxv-ef05487a05.json")
# default_app = firebase_admin.initialize_app(cred, {
#     'databaseURL': "https://nba-networks-default-rtdb.firebaseio.com/"
# })

# def load_play_by_play_data(year):
#     """
#     Load play-by-play data from a CSV file.
#     """
#     return pd.read_csv(f"data/play-by-play/nbastats_{year}.csv")

# def fetch_game_ids(play_by_play_data):
#     """
#     Extract unique game IDs from play-by-play data.
#     """
#     return pd.unique(play_by_play_data["GAME_ID"])

# def sanitize_key(key):
#     """
#     Sanitize a string to remove Firebase forbidden characters.
#     """
#     return re.sub(r'[.$#[\]/]', '', key)

# def get_play_by_play(game_id):
#     """
#     Fetch play-by-play data for a given game ID from NBA API.
#     """
#     game_id = f"00{game_id}"
#     try:
#         return playbyplayv2.PlayByPlayV2(game_id=game_id).play_by_play.get_data_frame()
#     except:
#         time.sleep(30)
#         try:
#             return playbyplayv2.PlayByPlayV2(game_id=game_id).play_by_play.get_data_frame()
#         except json.decoder.JSONDecodeError:
#             return None


# def filter_assist_data(all_games_combined):
#     """
#     Filter and transform play-by-play data to extract assist events.
#     """
#     ast_df = (
#         all_games_combined
#         .loc[
#             (all_games_combined.EVENTMSGTYPE == 1) &
#             (~all_games_combined.PLAYER2_ID.isna()) &
#             (all_games_combined.PLAYER2_ID != 0)
#         ]
#         .rename(columns={'PLAYER1_ID': 'SHOT_PLAYER', 'PLAYER2_ID': 'AST_PLAYER'})
#         .reset_index(drop=True)
#     )

#     cols = [
#         'SHOT_PLAYER', 'AST_PLAYER', 'HOME_PLAYER1', 'HOME_PLAYER2',
#         'HOME_PLAYER3', 'HOME_PLAYER4', 'HOME_PLAYER5',
#         'AWAY_PLAYER1', 'AWAY_PLAYER2', 'AWAY_PLAYER3',
#         'AWAY_PLAYER4', 'AWAY_PLAYER5'
#     ]

#     ast_df = ast_df[['HOMEDESCRIPTION', 'VISITORDESCRIPTION',
#                      'PLAYER1_TEAM_ABBREVIATION', 'PLAYER2_TEAM_ABBREVIATION'] + cols]
#     ast_df[cols] = ast_df[cols].apply(noc.players_name, result_type="expand")

#     return ast_df

# def add_other_players(ast_df):
#     """
#     Add columns for other players on the court during assist events.
#     """
#     cols = ['HOME_PLAYER1', 'HOME_PLAYER2', 'HOME_PLAYER3', 'HOME_PLAYER4', 'HOME_PLAYER5',
#             'AWAY_PLAYER1', 'AWAY_PLAYER2', 'AWAY_PLAYER3', 'AWAY_PLAYER4', 'AWAY_PLAYER5']

#     for i in range(1, 6):
#         ast_df[f'OTHER_PLAYER{i}'] = np.where(
#             ~ast_df['HOMEDESCRIPTION'].isna(), ast_df[f'HOME_PLAYER{i}'], ast_df[f'AWAY_PLAYER{i}']
#         )
#     ast_df["TEAM"] = ast_df["PLAYER1_TEAM_ABBREVIATION"]
#     return ast_df.dropna(subset=[f'OTHER_PLAYER{i}' for i in range(1, 6)], how='all').reset_index(drop=True)

# def create_assist_dict(filtered_ast_df, year):
#     """
#     Create a nested dictionary to store assist statistics organized by year, team, lineup, and players.
#     """
#     assist_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))

#     for _, row in filtered_ast_df.iterrows():
#         lineup = sorted([row[f'OTHER_PLAYER{i}'] for i in range(1, 6)])
#         lineup_str = sanitize_key('-'.join(lineup))
#         assist_player = sanitize_key(row['AST_PLAYER'])
#         shot_player = sanitize_key(row['SHOT_PLAYER'])
#         team = row['TEAM']

#         if year not in assist_dict:
#             assist_dict[year] = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
#         if team not in assist_dict[year]:
#             assist_dict[year][team] = defaultdict(lambda: defaultdict(int))
#         if lineup_str not in assist_dict[year][team]:
#             assist_dict[year][team][lineup_str] = defaultdict(int)
#         if assist_player not in assist_dict[year][team][lineup_str]:
#             assist_dict[year][team][lineup_str][assist_player] = defaultdict(int)

#         assist_dict[year][team][lineup_str][assist_player][shot_player] += 1

#     return convert_to_dict(assist_dict)


# def convert_to_dict(d):
#     if isinstance(d, defaultdict):
#         d = {k: convert_to_dict(v) for k, v in d.items()}
#     elif isinstance(d, dict):
#         d = {k: convert_to_dict(v) for k, v in d.items()}
#     return d


# def merge_assist_data(existing_data, new_data):
#     """
#     Merge new assist data into existing data structure.
#     """
#     for year, year_data in new_data.items():
#         if year not in existing_data:
#             existing_data[year] = year_data
#         else:
#             for team, team_data in year_data.items():
#                 if team not in existing_data[year]:
#                     existing_data[year][team] = team_data
#                 else:
#                     for lineup, lineup_data in team_data.items():
#                         if lineup not in existing_data[year][team]:
#                             existing_data[year][team][lineup] = lineup_data
#                         else:
#                             for assist_player, assist_player_data in lineup_data.items():
#                                 if assist_player not in existing_data[year][team][lineup]:
#                                     existing_data[year][team][lineup][assist_player] = assist_player_data
#                                 else:
#                                     for shot_player, count in assist_player_data.items():
#                                         if shot_player not in existing_data[year][team][lineup][assist_player]:
#                                             existing_data[year][team][lineup][assist_player][shot_player] = count
#                                         else:
#                                             existing_data[year][team][lineup][assist_player][shot_player] += count
#     return existing_data


# def clear_processed_games(year):
#     """
#     Clear the processed games tracker for a given year in Firebase.
#     """
#     db_ref = db.reference(f"processed_games/{year}")
#     db_ref.delete()
#     print(f"Cleared processed games tracker for year {year}.")

# def clear_conditional_assists():
#     """
#     Clear the conditional assists data in Firebase.
#     """
#     db_ref = db.reference("conditional_assist_networks")
#     db_ref.delete()
#     print("Cleared conditional assist networks in Firebase.")

# async def write_to_firebase_async(data, year):
#     """
#     Write data to Firebase asynchronously.
#     """
#     loop = asyncio.get_event_loop()
#     ref = db.reference(f"conditional_assist_networks/{year}")
#     await loop.run_in_executor(None, ref.update, data)
#     print(f"Data pushed to Firebase for year {year}.")

# async def write_game_ids_to_firebase_async(game_ids, year):
#     """
#     Write game IDs to Firebase asynchronously.
#     """
#     loop = asyncio.get_event_loop()
#     ref = db.reference(f"processed_games/{year}")
#     data = {sanitize_key(f"00{game_id}"): True for game_id in game_ids}
#     await loop.run_in_executor(None, ref.update, data)
#     print(f"Game IDs pushed to Firebase for year {year}.")


# def is_game_processed(game_id, year):
#     """
#     Check if the game ID has already been processed.
#     """
#     sanitized_game_id = f"00{game_id}"
#     db_ref = db.reference(f"processed_games_tracker/{year}/{sanitized_game_id}")
#     return db_ref.get() is not None

# async def process_play_by_play_async(game_ids, year):
#     all_games_data = []
#     assist_data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))
#     processed_game_ids = []

#     for idx, game_id in enumerate(game_ids):
#         if is_game_processed(game_id, year):
#             continue

#         try:
#             pbp = get_play_by_play(game_id)
#             if pbp is not None:
#                 pbp_with_players = noc.players_on_court(pbp)
#                 all_games_data.append(pbp_with_players)
#                 processed_game_ids.append(game_id)
#             else:
#                 continue
#         except KeyError:
#             continue
#         print(len(all_games_data))
#         if (idx + 1) % 25 == 0 or (idx + 1) == len(game_ids):
#             all_games_combined = pd.concat(all_games_data, ignore_index=True)
#             filtered_ast_df = filter_assist_data(all_games_combined)
#             filtered_ast_df = add_other_players(filtered_ast_df)
#             current_assist_data = create_assist_dict(filtered_ast_df, year)
#             assist_data = merge_assist_data(assist_data, current_assist_data)
#             await write_to_firebase_async(assist_data[year], year)
#             await write_game_ids_to_firebase_async(processed_game_ids, year)
#             all_games_data = []
#             processed_game_ids = []
#         print(f"Processed game {game_id} for year {year}.")

#     return assist_data

# def count_processed_game_ids(year):
#     db_ref = db.reference(f"processed_games/{year}")

#     processed_games = db_ref.get()

#     if processed_games:
#         num_games_processed = len(processed_games)
#         print(f"Number of processed game IDs for year {year}: {num_games_processed}")
#     else:
#         print(f"No processed game IDs found for year {year}.")


# async def main():
#     years = [2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022][::-1]  # 2023
#     # clear_conditional_assists()  # Clear the database at the beginning
#     for year in years:
#         count_processed_game_ids(year)
#         # clear_processed_games(year)
#         pbp_data = load_play_by_play_data(year)
#         season_games = fetch_game_ids(pbp_data)
#         assist_data = await process_play_by_play_async(season_games, year)
#         print(f"Processed data for year {year}: {assist_data}")

# if __name__ == "__main__":
#     asyncio.run(main())
