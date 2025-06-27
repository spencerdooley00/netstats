import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import bs4

def find_all_duplicates(lst):
    indices = {}
    duplicate_indices = {}

    for index, item in enumerate(lst):
        if item in indices:
            if item not in duplicate_indices:
                duplicate_indices[item] = [indices[item]]
            duplicate_indices[item].append(index)
        else:
            indices[item] = index

    return duplicate_indices
def main():
    true_positions = {"PG":0, "SG":1, "SF":2, "PF":3, "C":4}
    years = ["2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"]
    starting_lineups = {}
    for y, year in enumerate(years):
        url = f"https://basketball.realgm.com/nba/depth-charts/{year}"

        response = requests.get(url)
        content = response.content

        soup = BeautifulSoup(content, "html.parser")

        

        years_teams = [team_row.text.replace("Depth Chart", "").strip() for team_row in soup.find_all("h2", class_="clearfix")]
        teams = [" ".join(i.split(" ")[1:]) for i in years_teams]
        years = ["Season=" + i.split(" ")[0].split("-")[0] + "-" + i.split(" ")[0].split("-")[1][2:] for i in years_teams]
        print(years)
        starters_row_breakdown = [player_row for player_row in soup.find_all("tr", class_="depth_starters")]
        rotation_row_breakdown = [player_row for player_row in soup.find_all("tr", class_="depth_rotation")]
        starting_players = []
        starting_lineups[years[y]] = {}
        for i, entry in enumerate(starters_row_breakdown):
            starters = [' '.join(i['href'].split('/')[2].split('-')) for i in entry.find_all("a")]
            positions = [i['data-th'] for i in entry.find_all("td", class_="depth-chart-cell")]
    
            starting_lineups[years[y]][teams[i]] = {"starters": starters,
                                                    "positions": positions}
            if positions != list(true_positions.keys()):
                missing_pos = list(set(true_positions) - set(positions))[0]
                for s, sibling in enumerate(soup.find_all(class_="depth_starters")[i].next_siblings):
                    if isinstance(sibling, bs4.NavigableString):
                        continue
                    if isinstance(sibling, bs4.Tag):
                        rotation = [' '.join(l['href'].split('/')[2].split('-')) for l in sibling.find_all("a")]
                        rotation_positions = [p['data-th'] for p in sibling.find_all("td", class_="depth-chart-cell")]
                        rotation_positions_present = []
                        for j, pos in enumerate(rotation_positions):
                            if j == true_positions[pos]:
                                rotation_positions_present.append(pos)
                        missing_pos_index = rotation_positions_present.index(missing_pos)
                        replacement_player = rotation[missing_pos_index]
                        starting_lineups[years[y]][teams[i]]['starters'].append(replacement_player)
                        starting_lineups[years[y]][teams[i]]['positions'][true_positions[missing_pos]]= missing_pos
                    if s >0:
                        break

    with open("data/team_starting_lineups.json", "w") as file:
        json.dump(starting_lineups, file)

main()

