import json
from bs4 import BeautifulSoup
import requests
import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
import selenium
import chromedriver_autoinstaller


def has_exact_class(tag):
    return tag.name == "a" and tag.has_attr("class") and len(tag["class"]) == 1 and tag["class"][0] == "Anchor_anchor__cSc3P"


def get_player_img(player_id_num):
    r = requests.get(f"https://www.nba.com/stats/player/{player_id_num}")
    player_soup = BeautifulSoup(r.content, "html.parser")

    pic_links = player_soup.find_all(
        "img", class_="PlayerImage_image__wH_YX PlayerSummary_playerImage__sysif")

    for link in pic_links:
        return link['src']


def main(scrape_all=False):
    chromedriver_autoinstaller.install()

    options = webdriver.ChromeOptions()
    options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    chrome_driver_binary = "/opt/homebrew/bin/chromedriver"

    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument("--headless")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    options.add_argument('--window-size=1920,1080')

    teams = 'https://www.nba.com/teams'

    # Send a GET request to the URL and store the response
    response = requests.get(teams)

    # Parse the HTML content of the response using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    teams_links = soup.find_all(
        "a", class_="Anchor_anchor__cSc3P TeamFigureLink_teamFigureLink__uqnNO")
    # passing_data = {}
    with open('data/players/player_passing_data_all_years.json', 'r') as fp:
        passing_data = json.load(fp)
    with open('data/players/player_image_links.json', 'r') as f:
        player_image_dict = json.load(f)

    player_ids_scraped = set()
    seasons = ["Season=2013-14", "Season=2014-15", "Season=2015-16",
               "Season=2016-17", "Season=2017-18", "Season=2018-19",
               "Season=2019-20", "Season=2020-21", "Season=2021-22",
               "Season=2022-23", "Season=2023-24"]
    seasons = ["Season=2024-25"]
    for season in seasons:
        print(season)
        if season not in passing_data.keys():
            passing_data[season] = {}
        else:
            passing_data[season] = passing_data[season]

        if season not in player_image_dict.keys():
            player_image_dict[season] = {}
        else:
            player_image_dict[season] = player_image_dict[season]

        for teams_link in teams_links:
            if teams_link.text == 'Profile':
                team_name = teams_link['href'].split('/')[-2].title()
                if team_name not in list(passing_data[season].keys()):
                    passing_data[season][team_name] = {}
                else:
                    passing_data[season][team_name] = passing_data[season][team_name]
                if team_name not in list(player_image_dict[season].keys()):
                    player_image_dict[season][team_name] = {}
                print(team_name)
                driver = webdriver.Chrome(options=options)

                team_url = f"https://www.nba.com/stats/{'/'.join(teams_link['href'].split('/')[:-2])}?{season}"

                # Use Selenium to fetch the web page content
                driver.get(team_url)

                # Wait for the page to load (increase the timeout if necessary)
                wait = WebDriverWait(driver, 30)
                wait.until(EC.presence_of_element_located(
                    (By.CLASS_NAME, "Anchor_anchor__cSc3P")))

                # Get the page source after it's loaded
                page_source = driver.page_source
                # Close the driver once the page source is obtained
                driver.quit()
                # Now, you can continue parsing the page source using BeautifulSoup as before
                team_soup = BeautifulSoup(page_source, "html.parser")
                player_urls = team_soup.find_all(has_exact_class)
                player_names = [
                    player_link.text for player_link in player_urls]
                # if player_names == passing_data[season][team_name].keys():
                #     continue
                print(player_urls)
                for player_link in player_urls:
                    player_url = player_link["href"]

                    player_id_num = player_url.split('/')[-2]
                    player_name = player_link.text
                    # player_name = ' '.join(player_url.split('/')[3].split('-')).title()
                    player_img_link = get_player_img(player_id_num)
                    if player_name not in player_image_dict[season][team_name].keys():
                        player_image_dict[season][team_name][player_name] = player_img_link
                        with open('data/players/player_image_links.json', 'w') as f:
                            json.dump(player_image_dict, f)

                    if scrape_all or player_name not in passing_data[season][team_name].keys():
                        # Set up the Chrome driver
                        driver = webdriver.Chrome(options=options)

                        # Navigate to the page
                        player_url = f"https://www.nba.com/stats/player/{player_id_num}/passes-dash?{season}&SeasonType=Regular%20Season&dir=D&sort=PASS"
                        driver.get(player_url)

                        # Wait for the table to load
                        wait = WebDriverWait(driver, 10)
                        try:
                            table = wait.until(EC.presence_of_element_located(
                                (By.CSS_SELECTOR, ".Crom_table__p1iZz")))
                        except selenium.common.exceptions.TimeoutException:
                            continue

                        # Get the HTML of the table
                        table_html = table.get_attribute("outerHTML")
                        player_soup = BeautifulSoup(table_html, "html.parser")

                        passing_table = player_soup.find(
                            "table", class_="Crom_table__p1iZz")
                        # if passing_table is None:
                        #     # If no passing data is found, skip to the next player
                        #     continue
                        # # Initialize an empty dictionary to store the player's passing data
                        player_passing_data = {}
                        # Loop through each row of the passing table
                        for row in passing_table.find_all("tr")[2:]:
                            # Get the name of the player passed to
                            player_passed_to = row.find_all(
                                "td")[0].text.strip()
                            if len(player_passed_to.split(", ")) == 2:
                                last_name, first_name = player_passed_to.split(
                                    ", ")
                            else:
                                first_name = player_passed_to
                                last_name = ''
                            player_passed_to = "{} {}".format(
                                first_name, last_name)
                            # Get the number of passes to that player
                            num_passes = float(
                                row.find_all("td")[3].text.strip())
                            fgm_2pt = float(row.find_all("td")[8].text.strip())
                            fgm_3pt = float(row.find_all("td")
                                            [11].text.strip())
                            # Add the player and their number of passes to the player's passing data
                            player_passing_data[player_passed_to] = {
                                'freq': num_passes, 'ast_2pt': fgm_2pt, 'ast_3pt': fgm_3pt}

                        # Get the name of the player from their page title
                        driver.quit()
                        # Add the player and their passing data to the overall passing data dictionary
                        passing_data[season][team_name][player_name] = player_passing_data
                        print(player_name, team_name)
                        with open('data/players/player_passing_data_all_years.json', 'w') as fp:
                            json.dump(passing_data, fp)

    # def get_player_images():
    #     player_image_dict = {}
    #     soup = BeautifulSoup(response.content, "html.parser")
    #     teams_links = soup.find_all(
    #         "a", class_="Anchor_anchor__cSc3P TeamFigureLink_teamFigureLink__uqnNO")
    #     for teams_link in teams_links:
    #         if teams_link.text == 'Profile':
    #             team_name = teams_link['href'].split('/')[-2].title()
    #             team_soup = BeautifulSoup(requests.get(
    #                 f"https://www.nba.com{teams_link['href']}").content, "html.parser")
    #             for player_link in team_soup.find_all("a", class_="Anchor_anchor__cSc3P"):
    #                 if len(player_link['href'].split('/')) == 5 and 'player' in player_link['href']:
    #                     player_url = player_link["href"]
    #                     player_id_num = player_url.split('/')[2]
    #                     player_name = ' '.join(player_url.split(
    #                         '/')[3].split('-')).title().lower()
    #                     r = requests.get(
    #                         f"https://www.nba.com/stats/player/{player_id_num}")
    #                     player_soup = BeautifulSoup(r.content, "html.parser")

    #                     pic_links = player_soup.find_all(
    #                         "img", class_="PlayerImage_image__wH_YX PlayerSummary_playerImage__sysif")
    #                     for link in pic_links:
    #                         player_image_dict[player_name] = link['src']
