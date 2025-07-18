import requests
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import json
import re
import firebase_admin
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup

local_json_path = 'network_data/all_stats.json'
new_json_path = 'network_data/all_stats_test.json'
with open(local_json_path, 'r') as file:
    current_json = json.load(file)


def get_player_img(player_id_num, player_name=""):
    try:
        r = requests.get(f"https://www.nba.com/stats/player/{player_id_num}", 
        #                  proxies={
        #     'http': proxy,
        #     'https': proxy
        # }
                         )
    except (requests.exceptions.SSLError, requests.exceptions.ProxyError) as e:
        print("connection blocked... retrying")
        time.sleep(120)
        r = requests.get(f"https://www.nba.com/stats/player/{player_id_num}", 
        #                  proxies={
        #     'http': proxy,
        #     'https': proxy
        # }
                         )
    player_soup = BeautifulSoup(r.content, "html.parser")
    pic_links = player_soup.find_all(
        "img", class_="PlayerImage_image__wH_YX PlayerSummary_playerImage__sysif")

    if pic_links == []:
        player_name_code = "-".join(player_name.split(" ")).lower()
        r = requests.get(f"https://www.nba.com/stats/player/{player_id_num}/{player_name_code}", 
        #                  proxies={
        #     'http': proxy,
        #     'https': proxy
        # }
                         )
        player_soup = BeautifulSoup(r.content, "html.parser")
        pic_links = player_soup.find_all(
            "img", class_="PlayerImage_image__wH_YX PlayerSummary_playerImage__sysif")

    for link in pic_links:
        return link['src']


# cred = credentials.Certificate(
#     "nba-networks-firebase-adminsdk-twpxv-ef05487a05.json")

# default_app = firebase_admin.initialize_app(cred, {
#     'databaseURL': "https://nba-networks-default-rtdb.firebaseio.com/"
# })


player_headers = {
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Origin': 'https://www.nba.com',
    'Referer': 'https://www.nba.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Chrome',
    'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

player_params = {
    'DateFrom': '',
    'DateTo': '',
    'GameSegment': '',
    'ISTRound': '',
    'LastNGames': '0',
    'LeagueID': '00',
    'Location': '',
    'Month': '0',
    'OpponentTeamID': '0',
    'Outcome': '',
    'PORound': '0',
    'PerMode': 'PerGame',
    'Period': '0',
    'PlayerID': 'NA',
    'Season': 'NA',
    'SeasonSegment': '',
    'SeasonType': 'Regular Season',
    'TeamID': '0',
    'VsConference': '',
    'VsDivision': '',
}


headers = {
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Origin': 'https://www.nba.com',
    'Referer': 'https://www.nba.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
}

params = {
    'College': '',
    'Country': '',
    'DraftPick': '',
    'DraftRound': '',
    'DraftYear': '',
    'Height': '',
    'Historical': '0',
    'LeagueID': '00',
    'Season': 'NA',
    'SeasonType': 'Regular Season',
    'TeamID': '0',
    'Weight': '',
}


player_stats_headers = {
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Origin': 'https://www.nba.com',
    'Referer': 'https://www.nba.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
}

player_stats_params = {
    'College': '',
    'Conference': '',
    'Country': '',
    'DateFrom': '',
    'DateTo': '',
    'Division': '',
    'DraftPick': '',
    'DraftYear': '',
    'GameScope': '',
    'GameSegment': '',
    'Height': '',
    'ISTRound': '',
    'LastNGames': '0',
    'LeagueID': '00',
    'Location': '',
    'MeasureType': 'Base',
    'Month': '0',
    'OpponentTeamID': '0',
    'Outcome': '',
    'PORound': '0',
    'PaceAdjust': 'N',
    'PerMode': 'PerGame',
    'Period': '0',
    'PlayerExperience': '',
    'PlayerPosition': '',
    'PlusMinus': 'N',
    'Rank': 'N',
    'Season': '2023-24',
    'SeasonSegment': '',
    'SeasonType': 'Regular Season',
    'ShotClockRange': '',
    'StarterBench': '',
    'TeamID': '0',
    'VsConference': '',
    'VsDivision': '',
    'Weight': '',
}


lineups_headers = {
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Origin': 'https://www.nba.com',
    'Referer': 'https://www.nba.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Chrome',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
}

lineups_params = {
    'Conference': '',
    'DateFrom': '',
    'DateTo': '',
    'Division': '',
    'GameSegment': '',
    'GroupQuantity': '5',
    'ISTRound': '',
    'LastNGames': '0',
    'LeagueID': '00',
    'Location': '',
    'MeasureType': 'Base',
    'Month': '0',
    'OpponentTeamID': '0',
    'Outcome': '',
    'PORound': '0',
    'PaceAdjust': 'N',
    'PerMode': 'Totals',
    'Period': '0',
    'PlusMinus': 'N',
    'Rank': 'N',
    'Season': 'NA',
    'SeasonSegment': '',
    'SeasonType': 'Regular Season',
    'ShotClockRange': '',
    'TeamID': '',
    'VsConference': '',
    'VsDivision': '',
}


seasons = ["2013-14", "2014-15", "2015-16",
           "2016-17", "2017-18", "2018-19",
           "2019-20", "2020-21", "2021-22",
           "2022-23", "2023-24"]
seasons_to_update = ["2024-25"]

# url = 'http://ip.smartproxy.com/json'
# username = 'spguk5l34z'
# password = '0VSk7ngzzgxzlQw62Y'
# proxy = f"http://{username}:{password}@gate.smartproxy.com:10000"

# url = 'https://ip.smartproxy.com/json'
# username = 'spguk5l34z'
# password = '0VSk7ngzzgxzlQw62Y'
# proxy = f"http://{username}:{password}@gate.smartproxy.com:10001"
# result = requests.get(url, proxies = {
#     'http': proxy,
#     'https': proxy
# })
# print(result)


# def check_all_players_have_images(seasons):
#     for season in seasons:
#         season_data = db.reference(f"/all_stats/{season}").get()
#         for team in season_data.keys():
#             season_team_data = db.reference(f"/all_stats/{season}/{team}").get()
#             for player, p_dict in season_team_data.items():
#                 if "img" not in p_dict.keys():
#                     img = get_player_img(p_dict["stats"]["PLAYER_ID"])
#                     attr_ref = db.reference(f"/all_stats/{season}/{team}/{player}/img")
#                     attr_ref.set(img)


# seasons_to_update = ["2023-24"]
def run_script():
    # stats_dict = {}
    stats_dict = current_json
    for season in seasons_to_update:
        print(f"scraping {season}")
        stats_dict[season] = {}
        player_stats_params["Season"] = season
        try:
            game_stats_response = requests.get('https://stats.nba.com/stats/leaguedashplayerstats', params=player_stats_params, headers=player_stats_headers, 
            #                                    proxies={
            #     'http': proxy,
            #     'https': proxy
            # }
                                               )
        except ConnectionError:
            print("conn error")
            print("connection blocked... retrying")
            time.sleep(300)
            game_stats_response = requests.get('https://stats.nba.com/stats/leaguedashplayerstats', params=player_stats_params, headers=player_stats_headers, 
            #                                    proxies={
            #     'http': proxy,
            #     'https': proxy
            # }
                                               )
        response_headers = game_stats_response.json()[
            "resultSets"][0]["headers"]
        index_id = response_headers.index("PLAYER_ID")
        index_name = response_headers.index("PLAYER_NAME")
        index_team_abr = response_headers.index("TEAM_ABBREVIATION")
        index_team_id = response_headers.index("TEAM_ID")

        all_players = game_stats_response.json()["resultSets"][0]["rowSet"]

        lineups_params["Season"] = season
        try:
            lineups_response = requests.get(
                'https://stats.nba.com/stats/leaguedashlineups', params=lineups_params, headers=lineups_headers, 
                # proxies={
                #     'http': proxy,
                #     'https': proxy
                # }
                )
        except (requests.exceptions.SSLError, requests.exceptions.ProxyError) as e:
            print("connection blocked... retrying")
            time.sleep(120)
            lineups_response = requests.get(
                'https://stats.nba.com/stats/leaguedashlineups', params=lineups_params, headers=lineups_headers, 
                # proxies={
                #     'http': proxy,
                #     'https': proxy
                # }
                )

        for player_list in all_players:
            player_params["PlayerID"] = player_list[index_id]
            player_params["Season"] = season
            player_name = player_list[index_name]
            player_name = re.sub("['.]", "", player_name)
            print(player_name)
            # if player_name in stats_dict[season][player_list[index_team_abr]].keys():

            current_game_stats = dict(zip(response_headers, player_list))

            if player_list[index_team_abr] not in stats_dict[season].keys() and player_list[index_team_abr] is not None:
                stats_dict[season][player_list[index_team_abr]] = {}
            if player_list[index_team_abr] is not None and player_list[index_name] not in stats_dict[season][player_list[index_team_abr]].keys():
                stats_dict[season][player_list[index_team_abr]
                                   ][player_name] = {}
                try:
                    player_passes_response = requests.get(
                        'https://stats.nba.com/stats/playerdashptpass', params=player_params, headers=player_headers, 
                        # proxies={
                        #     'http': proxy,
                        #     'https': proxy
                        # }
                        )
                except (requests.exceptions.SSLError, requests.exceptions.ProxyError) as e:
                    print("connection blocked... retrying")
                    time.sleep(120)
                    player_passes_response = requests.get(
                        'https://stats.nba.com/stats/playerdashptpass', params=player_params, headers=player_headers, 
                        # proxies={
                        #     'http': proxy,
                        #     'https': proxy
                        # }
                        )
                try:
                    player_passing_headers = player_passes_response.json()[
                        "resultSets"][0]["headers"]
                    player_passing_data = player_passes_response.json()[
                        "resultSets"][0]["rowSet"]
                    pass_to_player_index = player_passing_headers.index(
                        "PASS_TO")
                    pass_to_player_passes_index = player_passing_headers.index(
                        "PASS")
                    pass_to_player_freq_index = player_passing_headers.index(
                        "FREQUENCY")
                    pass_to_player_assist_index = player_passing_headers.index(
                        "AST")
                    pass_to_player_2pt_fgm_index = player_passing_headers.index(
                        "FG2M")
                    pass_to_player_3pt_fmg_index = player_passing_headers.index(
                        "FG3M")
                    pass_to_player_2pt_fgp_index = player_passing_headers.index(
                        "FG2_PCT")
                    pass_to_player_3pt_fmp_index = player_passing_headers.index(
                        "FG3_PCT")

                    stats_dict[season][player_list[index_team_abr]
                                       ][player_name] = {"passes": {}, "stats": {}}
                    stats_dict[season][player_list[index_team_abr]
                                       ][player_name]["stats"] = current_game_stats
                    stats_dict[season][player_list[index_team_abr]
                                       ][player_name]["img"] = get_player_img(player_list[index_id])

               

                    try:
                        teams_players = list(
                            filter(lambda sublist: player_list[index_team_abr] in sublist, all_players))
                        team_player_ids = [sublist[0]
                                           for sublist in teams_players]
                        team_lineups = sorted(list(filter(lambda sublist: player_list[index_team_abr] in sublist, lineups_response.json()[
                            "resultSets"][0]["rowSet"])), key=lambda x: x[lineups_response.json()[
                                "resultSets"][0]["headers"].index("MIN")], reverse=True)
                        # all_lineups_p = {sublist[2] for sublist in sorted(team_lineups, key=lambda x: x[lineups_response.json()["resultSets"][0]["headers"].index("MIN")], reverse=True)}
                        # print(all_lineups_p)
                        all_lineups = [sublist[1] for sublist in team_lineups]
                        # all_lineups_p = {sublist[2] for sublist in sorted(team_lineups, key=lambda x: x[lineups_response.json()["resultSets"][0]["headers"].index("MIN")], reverse=True)}
                        # print(all_lineups_p)
                        # print(all_lineups)
                        for lineup in all_lineups:
                            lineup_players = [int(num)
                                              for num in lineup.split('-') if num]
                            if all(element in team_player_ids for element in lineup_players):
                                starters = lineup_players
                                break
                        if player_list[index_id] in starters:
                            stats_dict[season][player_list[index_team_abr]
                                               ][player_name]["is_starter"] = 1
                        else:
                            stats_dict[season][player_list[index_team_abr]
                                               ][player_name]["is_starter"] = 0
                    except requests.exceptions.JSONDecodeError:
                        stats_dict[season][player_list[index_team_abr]
                                           ][player_name]["is_starter"] = 0

                    for player_passed_to in player_passing_data:
                        try:
                            pass_to_player_name = ' '.join([player_passed_to[pass_to_player_index].split(
                                ", ")[1], player_passed_to[pass_to_player_index].split(", ")[0]])
                        except IndexError:
                            pass_to_player_name = player_passed_to[pass_to_player_index].split(", ")[
                                0]

                        pass_to_player_name = re.sub(
                            "['.]", "", pass_to_player_name)
                        player_pass_to_team = player_passed_to[4]
                        if player_pass_to_team == player_list[index_team_abr]:
                            stats_dict[season][player_list[index_team_abr]][player_name]["passes"][pass_to_player_name] = {
                                "passes": player_passed_to[pass_to_player_passes_index],
                                "freq": player_passed_to[pass_to_player_freq_index],
                                "ast": player_passed_to[pass_to_player_assist_index],
                                "fg2m": player_passed_to[pass_to_player_2pt_fgm_index],
                                "fg3m": player_passed_to[pass_to_player_3pt_fmg_index],
                                "fg2pct": player_passed_to[pass_to_player_2pt_fgp_index],
                                "fg3pct": player_passed_to[pass_to_player_3pt_fmp_index]
                            }

                except requests.exceptions.JSONDecodeError:
                    pass

        now = datetime.now()
        dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
        stats_dict[season]["time_scraped"] = dt_string
        # attr_ref = db.reference(f"/all_stats/{season}")
        # attr_ref.set(stats_dict[season])
        # print(f"Pushed {season} to firebase...")
        with open(new_json_path, 'w') as file:
            json.dump(stats_dict, file)
            print('written')
      


run_script()