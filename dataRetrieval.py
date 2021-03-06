#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import requests
from riotwatcher import LolWatcher, ApiError
import json
import pickle
from tqdm import tqdm
import time
from bs4 import BeautifulSoup
from requests import get
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

pd.set_option('display.max_columns', 150)

pd.set_option('display.max_rows', 15000)

# Notes
# Team Id: 100 = Blue side
# Team Id: 200 = Red side
# Blue Team Gold Difference
# Blue Team Vision Difference
# Blue Team Gold Difference
# GOld eearned,
# Gold Spent
# Expereince difference
#


# Delete any rows in which the summoner name is no longer valid (change summoner name), so can't get champ winrate and kda
# Some games have "None" values for the roles, so maybe disregard those partiuclar role, not sure yet

API_KEY = "RGAPI-64bcb52d-1ccb-4fc5-a7ec-8050226f63bb"
PLATFORM_ROUTING_VALUE = "na1.api.riotgames.com"
REGIONAL_ROUTING_VALUE = "americas.api.riotgames.com"
watcher = LolWatcher(API_KEY)
region = "na1"

if __name__ == "__main__":
    query = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/Doublelift?api_key={API_KEY}"
    response = requests.get(query)
    me = watcher.summoner.by_name(region, "hide on bush")

    my_ranked_stats = watcher.league.by_summoner(region, me['id'])

    columns = ["summoner-rank", ]
    df = pd.DataFrame()
    df.append(my_ranked_stats)

    bb = watcher.match.matchlist_by_account('na1', "6EUVgfrJtCR2B1P5o3bo8DhyjcyPC92er5ihmfJm9LrgFFk")

    with open('data/10.16.1/data/en_US/champion.json') as json_file:
        champion_data = json.load(json_file)

    champ2index = {}
    index2champ = {}
    for champ in champion_data['data']:
        champ2index[champ] = int(champion_data["data"][champ]["key"])
        index2champ[int(champion_data["data"][champ]["key"])] = champ

    challenger_korea = "T1 BurdoI"
    challenger_north_america = "C9 Zven"
    challenger_europe = "Agurin"
    challenger_players = [('kr', challenger_korea), ('na1', challenger_north_america), ('euw1', challenger_europe)]

    # players = [(x, watcher.summoner.by_name(x, y)['accountId']) for (x, y) in challenger_players]
    #
    # print(players)
    #
    # gameIDs = []
    # matches = pd.DataFrame()

    matches = pd.read_pickle("updatedMatches3.pickle")

    with open("players3.pickle", 'rb') as pick:
        players = pickle.load(pick)
    with open("gameId3.pickle", "rb") as pick:
        gameIDs = pickle.load(pick)

    with open("champ2winrateNA.pickle", 'rb') as pick:
        champ2winrateNA = pickle.load(pick)
    with open("champ2winrateEUW.pickle", 'rb') as pick:
        champ2winrateEUW = pickle.load(pick)
    with open("champ2winrateKR.pickle", 'rb') as pick:
        champ2winrateKR = pickle.load(pick)

    item2index = {}
    index2item = {}
    with open('data/10.16.1/data/en_US/item.json') as json_file:
        item_data = json.load(json_file)
    for item in item_data['data']:
        item2index[item_data['data'][item]['name']] = item
        index2item[item] = item_data['data'][item]['name']

    champ2champ = {}

    for x in champ2index.keys():
        champ2champ[x] = x
    for x in champ2champ.keys():
        upper = [(index, y) for index, y in enumerate(x) if y.isupper()]
        if len(upper) > 1:
            champ2champ[x] = x[0:upper[1][0]] + " " + x[upper[1][0]: len(x) + 1]

    champ2champ["MonkeyKing"] = "Wukong"
    champ2champ["Kaisa"] = "Kai'Sa"
    champ2champ["Chogath"] = "Cho'Gath"
    champ2champ["Khazix"] = "Kha'Zix"
    champ2champ["KogMaw"] = "Kog'Maw"
    champ2champ["RekSai"] = "Rek'Sai"
    champ2champ["Velkoz"] = "Vel'Koz"
    champ2champ["DrMundo"] = "Dr. Mundo"
    champ2champ["Leblanc"] = "LeBlanc"
    champ2champ["Nunu"] = "Nunu & Willump"


    def checkNameUsed(region, username):
        if region == "KR":
            region = "www."
        elif region == "NA1":
            region = "na."
        elif region == "EUW1":
            region = "euw."
        url = f"https://{region}op.gg/summoner/userName={username}"
        response = get(url).text
        soup = BeautifulSoup(response, 'html.parser')
        return soup.find(text=f"{username}") is not None


    def getWinRatio(region, username, currentChampion):
        if region == "KR":
            region = "www."
        elif region == "NA1":
            region = "na."
        elif region == "EUW1":
            region = "euw."
        url = f"https://{region}op.gg/summoner/champions/userName={username}"
        response = get(url).text
        soup = BeautifulSoup(response, 'html.parser')
        try:
            return int(
                str(soup.find(text=currentChampion).parent.parent.parent.parent.find("span", {"class": "WinRatio"}).text)[
                :-1])
        except Exception as e:
            print("Region: ", region)
            print("Username: ", username)
            print("Champion: ", currentChampion)
            print("Exception: ", e)
            print(url)
            return -1


    def getChampKDA(region, username, currentChampion):
        if region == "KR":
            region = "www."
        elif region == "NA1":
            region = "na."
        elif region == "EUW1":
            region = "euw."
        url = f"https://{region}op.gg/summoner/champions/userName={username}"
        response = get(url).text
        soup = BeautifulSoup(response, 'html.parser')


        try:
            return float(
            soup.find(text=currentChampion).parent.parent.parent.parent.find("td", {"class": "KDA"})['data-value'])
        except Exception as e:
            print("Region: ", region)
            print("Username: ", username)
            print("Champion: ", currentChampion)
            print("Exception: ", e)
            print(url)
            return -1


    def getChampGames(region, username, currentChampion):
        if region == "KR":
            region = "www."
        elif region == "NA1":
            region = "na."
        elif region == "EUW1":
            region = "euw."
        url = f"https://{region}op.gg/summoner/champions/userName={username}"
        response = get(url).text
        soup = BeautifulSoup(response, 'html.parser')

        try:
            wins = int(
                soup.find(text=currentChampion).parent.parent.parent.parent.find("div", {"class": "Text Left"}).text[
                :-1])
        except:
            wins = 0
        try:
            losses = int(
                soup.find(text=currentChampion).parent.parent.parent.parent.find("div", {"class": "Text Right"}).text[
                :-1])
        except:
            losses = 0

        return wins + losses


    def getChampWinRate(region, currentChampion):
        if region == "KR":
            region = "www."
        elif region == "NA1":
            region = "na."
        elif region == "EUW1":
            region = "euw."
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        url = f"https://{region}op.gg/statistics/champion/"
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        return soup.find(text=currentChampion).parent.parent.parent.findAll("td")[3]['data-value']


    # print(matches.shape)
    # with open("blue1champWinRates.pickle", "rb") as pick:
    #     l = pickle.load(pick)
    # with open("blue2champWinRates.pickle", "rb") as pick:
    #     l2 = pickle.load(pick)
    # for index, x in enumerate(l):
    #     l[index] = x.tolist()[0]
    # for index, x in enumerate(l2):
    #     l2[index] = x.tolist()[0]
    # bad_indices = []
    # for index, x in enumerate(l):
    #     if x == -1:
    #         bad_indices.append(index)
    # bad_indices2 = []
    # for index, x, in enumerate(l2):
    #     if x == -1:
    #         bad_indices2.append(index)
    # total_bad_indices = set(bad_indices + bad_indices2)
    # bad_players = matches.iloc[bad_indices, :]["participantIdentities"].apply(lambda x: x[0]['player']['summonerName'])
    # bad_players2 = matches.iloc[bad_indices2, :]['participantIdentities'].apply(
    #     lambda x: x[1]['player']['summonerName'])
    # total_bad_players = bad_players.tolist() + bad_players2.tolist()
    #
    #
    # def checkBadParticipants(summonerList):
    #     for summoner in summonerList:
    #         if summoner['player']['summonerName'] in total_bad_players:
    #             return True
    #     return False
    #
    #
    # all_bad_indices = matches.apply(lambda x: checkBadParticipants(x['participantIdentities']), axis=1)
    # all_bad_indices = all_bad_indices.tolist()
    # all_bad_indices_updated = []
    # for index, truth in enumerate(all_bad_indices):
    #     if truth:
    #         all_bad_indices_updated.append(index)
    # print(len(all_bad_indices_updated))
    # print(all_bad_indices_updated)
    # matches = matches.drop(list(matches.iloc[all_bad_indices_updated].index))
    # print(matches.shape)
    # matches.to_pickle("updatedMatches2.pickle")

# ADDING COLUMNS TO MATCHES
# matches["Blue Side Win"] = matches["teams"].apply(lambda x: x[0]['win'])
# matches["Blue Side First Dragon"] = matches["teams"].apply(lambda x: x[0]['firstDragon'])
# matches["Blue Side First Blood"] = matches["teams"].apply(lambda x: x[0]['firstBlood'])
# matches["Blue Side Towers Destroyed"] = matches["teams"].apply(lambda x: x[0]['towerKills'])
# matches["Blue Side First Baron"] = matches["teams"].apply(lambda x: x[0]['firstBaron'])
# matches["Blue Side First Tower"] = matches["teams"].apply(lambda x: x[0]['firstTower'])

# matches["Blue Side Inhibitors Destroyed"] = matches["teams"].apply(lambda x: x[0]['inhibitorKills'])
# matches["Blue Side Baron Kills"] = matches["teams"].apply(lambda x: x[0]['baronKills'])
# matches["Blue Side RiftHerald Kills"] = matches["teams"].apply(lambda x: x[0]['riftHeraldKills'])
# matches["Red Side Towers Destroyed"] = matches["teams"].apply(lambda x: x[1]['towerKills'])
# matches["Red Side Inhibitors Destroyed"] = matches["teams"].apply(lambda x: x[1]['inhibitorKills'])
# matches["Red Side Baron Kills"] = matches["teams"].apply(lambda x: x[1]['baronKills'])
# matches["Red Side RiftHerald Kills"] = matches["teams"].apply(lambda x: x[1]['riftHeraldKills'])

# matches["Blue Side Player 1 Kills"] = matches["participants"].apply(lambda x: x[0]['stats']['kills'])
# matches["Blue Side Player 1 Deaths"] = matches["participants"].apply(lambda x: x[0]['stats']['deaths'])
# matches["Blue Side Player 1 Assists"] = matches["participants"].apply(lambda x: x[0]['stats']['assists'])
# matches["Blue Side Player 1 Role"] = matches["participants"].apply(lambda x: x[0]['timeline']['lane'] if x[0]['timeline']['lane'] != "BOTTOM" else x[0]['timeline']['role'])
# matches["Blue Side Player 1 Gold Earned"] = matches["participants"].apply(lambda x: x[0]['stats']['goldEarned'])
# matches["Blue Side Player 1 Gold Spent"] = matches["participants"].apply(lambda x: x[0]['stats']['goldSpent'])
# matches["Blue Side Player 1 Champ Level"] = matches["participants"].apply(lambda x: x[0]['stats']['champLevel'])
# matches["Blue Side Player 1 Wards Placed"] = matches["participants"].apply(lambda x: x[0]['stats']['wardsPlaced'])
# matches["Blue Side Player 1 Vision Score"] = matches["participants"].apply(lambda x: x[0]['stats']['visionScore'])
# matches["Blue Side Player 1 Champion"] = matches["participants"].apply(lambda x: champ2champ[index2champ[x[0]['championId']]])
# # matches["Blue Side Player 1 Champion Win Ratio"] = matches.apply(lambda x: getWinRatio(x['platformId'], x['participantIdentities'][0]['player']['summonerName'], x['Blue Side Player 1 Champion']), axis = 1)

# matches["Blue Side Player 2 Kills"] = matches["participants"].apply(lambda x: x[1]['stats']['kills'])
# matches["Blue Side Player 2 Deaths"] = matches["participants"].apply(lambda x: x[1]['stats']['deaths'])
# matches["Blue Side Player 2 Assists"] = matches["participants"].apply(lambda x: x[1]['stats']['assists'])
# matches["Blue Side Player 2 Role"] = matches["participants"].apply(lambda x: x[1]['timeline']['lane'] if x[1]['timeline']['lane'] != "BOTTOM" else x[1]['timeline']['role'])
# matches["Blue Side Player 2 Gold Earned"] = matches["participants"].apply(lambda x: x[1]['stats']['goldEarned'])
# matches["Blue Side Player 2 Gold Spent"] = matches["participants"].apply(lambda x: x[1]['stats']['goldSpent'])
# matches["Blue Side Player 2 Champ Level"] = matches["participants"].apply(lambda x: x[1]['stats']['champLevel'])
# matches["Blue Side Player 2 Wards Placed"] = matches["participants"].apply(lambda x: x[1]['stats']['wardsPlaced'])
# matches["Blue Side Player 2 Vision Score"] = matches["participants"].apply(lambda x: x[1]['stats']['visionScore'])
# matches["Blue Side Player 2 Champion"] = matches["participants"].apply(lambda x: champ2champ[index2champ[x[1]['championId']]])
# # matches["Blue Side Player 1 Champion Win Ratio"] = matches.apply(lambda x: getWinRatio(x['platformId'], x['participantIdentities'][0]['player']['summonerName'], x['Blue Side Player 2 Champion']), axis = 1)


# matches["Blue Side Player 3 Kills"] = matches["participants"].apply(lambda x: x[2]['stats']['kills'])
# matches["Blue Side Player 3 Deaths"] = matches["participants"].apply(lambda x: x[2]['stats']['deaths'])
# matches["Blue Side Player 3 Assists"] = matches["participants"].apply(lambda x: x[2]['stats']['assists'])
# matches["Blue Side Player 3 Role"] = matches["participants"].apply(lambda x: x[2]['timeline']['lane'] if x[2]['timeline']['lane'] != "BOTTOM" else x[2]['timeline']['role'])
# matches["Blue Side Player 3 Gold Earned"] = matches["participants"].apply(lambda x: x[2]['stats']['goldEarned'])
# matches["Blue Side Player 3 Gold Spent"] = matches["participants"].apply(lambda x: x[2]['stats']['goldSpent'])
# matches["Blue Side Player 3 Champ Level"] = matches["participants"].apply(lambda x: x[2]['stats']['champLevel'])
# matches["Blue Side Player 3 Wards Placed"] = matches["participants"].apply(lambda x: x[2]['stats']['wardsPlaced'])
# matches["Blue Side Player 3 Vision Score"] = matches["participants"].apply(lambda x: x[2]['stats']['visionScore'])
# matches["Blue Side Player 3 Champion"] = matches["participants"].apply(lambda x: champ2champ[index2champ[x[2]['championId']]])


# matches["Blue Side Player 4 Kills"] = matches["participants"].apply(lambda x: x[3]['stats']['kills'])
# matches["Blue Side Player 4 Deaths"] = matches["participants"].apply(lambda x: x[3]['stats']['deaths'])
# matches["Blue Side Player 4 Assists"] = matches["participants"].apply(lambda x: x[3]['stats']['assists'])
# matches["Blue Side Player 4 Role"] = matches["participants"].apply(lambda x: x[3]['timeline']['lane'] if x[3]['timeline']['lane'] != "BOTTOM" else x[3]['timeline']['role'])
# matches["Blue Side Player 4 Gold Earned"] = matches["participants"].apply(lambda x: x[3]['stats']['goldEarned'])
# matches["Blue Side Player 4 Gold Spent"] = matches["participants"].apply(lambda x: x[3]['stats']['goldSpent'])
# matches["Blue Side Player 4 Champ Level"] = matches["participants"].apply(lambda x: x[3]['stats']['champLevel'])
# matches["Blue Side Player 4 Wards Placed"] = matches["participants"].apply(lambda x: x[3]['stats']['wardsPlaced'])
# matches["Blue Side Player 4 Vision Score"] = matches["participants"].apply(lambda x: x[3]['stats']['visionScore'])
# matches["Blue Side Player 4 Champion"] = matches["participants"].apply(lambda x: champ2champ[index2champ[x[3]['championId']]])


# matches["Blue Side Player 5 Kills"] = matches["participants"].apply(lambda x: x[4]['stats']['kills'])
# matches["Blue Side Player 5 Deaths"] = matches["participants"].apply(lambda x: x[4]['stats']['deaths'])
# matches["Blue Side Player 5 Assists"] = matches["participants"].apply(lambda x: x[4]['stats']['assists'])
# matches["Blue Side Player 5 Role"] = matches["participants"].apply(lambda x: x[4]['timeline']['lane'] if x[4]['timeline']['lane'] != "BOTTOM" else x[4]['timeline']['role'])
# matches["Blue Side Player 5 Gold Earned"] = matches["participants"].apply(lambda x: x[4]['stats']['goldEarned'])
# matches["Blue Side Player 5 Gold Spent"] = matches["participants"].apply(lambda x: x[4]['stats']['goldSpent'])
# matches["Blue Side Player 5 Champ Level"] = matches["participants"].apply(lambda x: x[4]['stats']['champLevel'])
# matches["Blue Side Player 5 Wards Placed"] = matches["participants"].apply(lambda x: x[4]['stats']['wardsPlaced'])
# matches["Blue Side Player 5 Vision Score"] = matches["participants"].apply(lambda x: x[4]['stats']['visionScore'])
# matches["Blue Side Player 5 Champion"] = matches["participants"].apply(lambda x: champ2champ[index2champ[x[4]['championId']]])

# matches["Red Side Player 1 Kills"] = matches["participants"].apply(lambda x: x[5]['stats']['kills'])
# matches["Red Side Player 1 Deaths"] = matches["participants"].apply(lambda x: x[5]['stats']['deaths'])
# matches["Red Side Player 1 Assists"] = matches["participants"].apply(lambda x: x[5]['stats']['assists'])
# matches["Red Side Player 1 Role"] = matches["participants"].apply(lambda x: x[5]['timeline']['lane'] if x[5]['timeline']['lane'] != "BOTTOM" else x[5]['timeline']['role'])
# matches["Red Side Player 1 Gold Earned"] = matches["participants"].apply(lambda x: x[5]['stats']['goldEarned'])
# matches["Red Side Player 1 Gold Spent"] = matches["participants"].apply(lambda x: x[5]['stats']['goldSpent'])
# matches["Red Side Player 1 Champ Level"] = matches["participants"].apply(lambda x: x[5]['stats']['champLevel'])
# matches["Red Side Player 1 Wards Placed"] = matches["participants"].apply(lambda x: x[5]['stats']['wardsPlaced'])
# matches["Red Side Player 1 Vision Score"] = matches["participants"].apply(lambda x: x[5]['stats']['visionScore'])
# matches["Red Side Player 1 Champion"] = matches["participants"].apply(lambda x: champ2champ[index2champ[x[5]['championId']]])


# matches["Red Side Player 2 Kills"] = matches["participants"].apply(lambda x: x[6]['stats']['kills'])
# matches["Red Side Player 2 Deaths"] = matches["participants"].apply(lambda x: x[6]['stats']['deaths'])
# matches["Red Side Player 2 Assists"] = matches["participants"].apply(lambda x: x[6]['stats']['assists'])
# matches["Red Side Player 2 Role"] = matches["participants"].apply(lambda x: x[6]['timeline']['lane'] if x[6]['timeline']['lane'] != "BOTTOM" else x[6]['timeline']['role'])
# matches["Red Side Player 2 Gold Earned"] = matches["participants"].apply(lambda x: x[6]['stats']['goldEarned'])
# matches["Red Side Player 2 Gold Spent"] = matches["participants"].apply(lambda x: x[6]['stats']['goldSpent'])
# matches["Red Side Player 2 Champ Level"] = matches["participants"].apply(lambda x: x[6]['stats']['champLevel'])
# matches["Red Side Player 2 Wards Placed"] = matches["participants"].apply(lambda x: x[6]['stats']['wardsPlaced'])
# matches["Red Side Player 2 Vision Score"] = matches["participants"].apply(lambda x: x[6]['stats']['visionScore'])
# matches["Red Side Player 2 Champion"] = matches["participants"].apply(lambda x: champ2champ[index2champ[x[6]['championId']]])


# matches["Red Side Player 3 Kills"] = matches["participants"].apply(lambda x: x[7]['stats']['kills'])
# matches["Red Side Player 3 Deaths"] = matches["participants"].apply(lambda x: x[7]['stats']['deaths'])
# matches["Red Side Player 3 Assists"] = matches["participants"].apply(lambda x: x[7]['stats']['assists'])
# matches["Red Side Player 3 Role"] = matches["participants"].apply(lambda x: x[7]['timeline']['lane'] if x[7]['timeline']['lane'] != "BOTTOM" else x[7]['timeline']['role'])
# matches["Red Side Player 3 Gold Earned"] = matches["participants"].apply(lambda x: x[7]['stats']['goldEarned'])
# matches["Red Side Player 3 Gold Spent"] = matches["participants"].apply(lambda x: x[7]['stats']['goldSpent'])
# matches["Red Side Player 3 Champ Level"] = matches["participants"].apply(lambda x: x[7]['stats']['champLevel'])
# matches["Red Side Player 3 Wards Placed"] = matches["participants"].apply(lambda x: x[7]['stats']['wardsPlaced'])
# matches["Red Side Player 3 Vision Score"] = matches["participants"].apply(lambda x: x[7]['stats']['visionScore'])
# matches["Red Side Player 3 Champion"] = matches["participants"].apply(lambda x: champ2champ[index2champ[x[7]['championId']]])


# matches["Red Side Player 4 Kills"] = matches["participants"].apply(lambda x: x[8]['stats']['kills'])
# matches["Red Side Player 4 Deaths"] = matches["participants"].apply(lambda x: x[8]['stats']['deaths'])
# matches["Red Side Player 4 Assists"] = matches["participants"].apply(lambda x: x[8]['stats']['assists'])
# matches["Red Side Player 4 Role"] = matches["participants"].apply(lambda x: x[8]['timeline']['lane'] if x[8]['timeline']['lane'] != "BOTTOM" else x[8]['timeline']['role'])
# matches["Red Side Player 4 Gold Earned"] = matches["participants"].apply(lambda x: x[8]['stats']['goldEarned'])
# matches["Red Side Player 4 Gold Spent"] = matches["participants"].apply(lambda x: x[8]['stats']['goldSpent'])
# matches["Red Side Player 4 Champ Level"] = matches["participants"].apply(lambda x: x[8]['stats']['champLevel'])
# matches["Red Side Player 4 Wards Placed"] = matches["participants"].apply(lambda x: x[8]['stats']['wardsPlaced'])
# matches["Red Side Player 4 Vision Score"] = matches["participants"].apply(lambda x: x[8]['stats']['visionScore'])
# matches["Red Side Player 4 Champion"] = matches["participants"].apply(lambda x: champ2champ[index2champ[x[8]['championId']]])


# matches["Red Side Player 5 Kills"] = matches["participants"].apply(lambda x: x[9]['stats']['kills'])
# matches["Red Side Player 5 Deaths"] = matches["participants"].apply(lambda x: x[9]['stats']['deaths'])
# matches["Red Side Player 5 Assists"] = matches["participants"].apply(lambda x: x[9]['stats']['assists'])
# matches["Red Side Player 5 Role"] = matches["participants"].apply(lambda x: x[9]['timeline']['lane'] if x[9]['timeline']['lane'] != "BOTTOM" else x[9]['timeline']['role'])
# matches["Red Side Player 5 Gold Earned"] = matches["participants"].apply(lambda x: x[9]['stats']['goldEarned'])
# matches["Red Side Player 5 Gold Spent"] = matches["participants"].apply(lambda x: x[9]['stats']['goldSpent'])
# matches["Red Side Player 5 Champ Level"] = matches["participants"].apply(lambda x: x[9]['stats']['champLevel'])
# matches["Red Side Player 5 Wards Placed"] = matches["participants"].apply(lambda x: x[9]['stats']['wardsPlaced'])
# matches["Red Side Player 5 Vision Score"] = matches["participants"].apply(lambda x: x[9]['stats']['visionScore'])
# matches["Red Side Player 5 Champion"] = matches["participants"].apply(lambda x: champ2champ[index2champ[x[9]['championId']]])

# # champ2winrateNA = {}
# # champ2winrateKR = {}
# # champ2winrateEUW = {}
# for key in list(champ2champ.keys())[120:]:
#     print(key)
#     time.sleep(1)
#     champ2winrateNA[champ2champ[key]] = getChampWinRate("NA1", champ2champ[key])
#     champ2winrateKR[champ2champ[key]] = getChampWinRate("KR", champ2champ[key])
#     champ2winrateEUW[champ2champ[key]] = getChampWinRate("EUW1", champ2champ[key])


# has_valid_player10 = matches.apply(lambda x: checkNameUsed(x['platformId'], x['participantIdentities'][9]['player']['summonerName']), axis=1)

# (has_valid_player10 == True).sum()
# (has_valid_player10 == False).sum()

# valid_player10_indices = has_valid_player10[has_valid_player10 == False].index
# list(valid_player10_indices)
# temp_matches = matches.copy()
# temp_matches.head()['participantIdentities']
# participantList = temp_matches.apply(lambda x: [(x['platformId'], p['player']['summonerName']) for p in x['participantIdentities']], axis = 1)
# participantList.head(10)

# unused_names = temp_matches.apply(lambda x: (x['platformId'], x['participantIdentities'][9]['player']['summonerName']), axis = 1)
# unused_names = unused_names[valid_player10_indices]
# unused_names.head(150)

# total_unusable_rows = []
# which_unused = []
# for index, participants in enumerate(participantList):
#     for unused in list(unused_names):
#         if unused in participants:
#             total_unusable_rows.append(index)
#             which_unused.append(unused)
# which_unused
# total_unusable_rows = list(set(total_unusable_rows))
# temp_matches = temp_matches.drop(total_unusable_rows)
# temp_matches.to_pickle("matches_filtered.pickle")


# cur_index = 200
# while 1 == 1:
#     try:
#         for player in players[cur_index:]:
#             cur_index +=1
#             cur_region, cur_player = player
#             print(cur_region, cur_player)
#             player_matches = watcher.match.matchlist_by_account(cur_region, cur_player)
#             for match in tqdm(player_matches["matches"]):
#                 # time.sleep(0.5)
#                 match_details = watcher.match.by_id(cur_region, match['gameId'])
#                 if match_details["queueId"] != 420:
#                     print("Not SoloQueue")
#                     continue
#                 if match["gameId"] not in gameIDs:
#                     gameIDs.append(match['gameId'])
#                     print("Match is NOT already collected")
#                 else:
#                     print("Match is already collected")
#                     continue
#                 # time.sleep(0.5)
#                 matches = matches.append(match_details, ignore_index=True)
#                 for participant in tqdm(match_details["participantIdentities"]):
#                     if (cur_region, participant["player"]["accountId"]) not in players:
#
#                         players.append((cur_region, participant["player"]["accountId"]))
#                 # time.sleep(0.5)
#     except KeyboardInterrupt:
#         print("Exception occured")
#         matches.to_pickle("temp2.pickle")
#         with open("players.pickle2", 'wb') as pick:
#             pickle.dump(players, pick)
#         with open("gameId.pickle2", 'wb') as pick:
#             pickle.dump(gameIDs, pick)
#         print("SAFE TO STOP 1")
#     except requests.exceptions.HTTPError:
#         print("SERVER ERROR")
#         matches.to_pickle("temp3.pickle")
#         with open("players3.pickle", 'wb') as pick:
#             pickle.dump(players, pick)
#         with open("gameId3.pickle", 'wb') as pick:
#             pickle.dump(gameIDs, pick)
#         print("SAFE TO STOP 2")





# print(x)

blue1champWinRates = []
blue2champWinRates = []
blue3champWinRates = []
blue4champWinRates = []
blue5champWinRates = []

red1champWinRates = []
red2champWinRates = []
red3champWinRates = []
red4champWinRates = []
red5champWinRates = []

blue1champKDA = []
blue2champKDA = []
blue3champKDA = []
blue4champKDA = []
blue5champKDA = []

red1champKDA = []
red2champKDA = []
red3champKDA = []
red4champKDA = []
red5champKDA = []

blue1champMatches = []
blue2champMatches = []
blue3champMatches = []
blue4champMatches = []
blue5champMatches = []

red1champMatches = []
red2champMatches = []
red3champMatches = []
red4champMatches = []
red5champMatches = []

blue1champPatchWinRate = []
blue2champPatchWinRate = []
blue3champPatchWinRate = []
blue4champPatchWinRate = []
blue5champPatchWinRate = []

red1champPatchWinRate = []
red2champPatchWinRate = []
red3champPatchWinRate = []
red4champPatchWinRate = []
red5champPatchWinRate = []
# # matches["Blue Side Player 1 Champion Win Ratio"] = matches.apply(lambda x: getWinRatio(x['platformId'], x['participantIdentities'][0]['player']['summonerName'], x['Blue Side Player 1 Champion']), axis = 1)
print()

# for x in tqdm(range(len(matches))):
#     # try:
#     blue1champWinRates.append(matches.iloc[x:x + 1, :].apply(lambda x: getWinRatio(x['platformId'], x['participantIdentities'][0]['player']['summonerName'], champ2champ[index2champ[x['participants'][0]['championId']]]), axis = 1))
#     # except Exception as e:
#     #     print("Index: ", x, " with exception: ", e)
#     #     time.sleep(125)
#     #     blue1champWinRates.append(matches.iloc[x:x + 1, :].apply(
#     #         lambda x: getWinRatio(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
#     #                               x['Blue Side Player 1 Champion']), axis = 1))
#     #     print("SHOULD BE FIXED NOW")
# with open("blue1champWinRates2.pickle", 'wb') as pick:
#     pickle.dump(blue1champWinRates, pick)
#
# for x in tqdm(range(len(matches))):
#     # try:
#     blue2champWinRates.append(matches.iloc[x:x + 1, :].apply(lambda x: getWinRatio(x['platformId'], x['participantIdentities'][1]['player']['summonerName'], champ2champ[index2champ[x['participants'][1]['championId']]]), axis = 1))
#     # except Exception as e:
#     #     print("Index: ", x, " with exception: ", e)
#     #     time.sleep(125)
#     #     blue1champWinRates.append(matches.iloc[x:x + 1, :].apply(
#     #         lambda x: getWinRatio(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
#     #                               x['Blue Side Player 1 Champion']), axis = 1))
#     #     print("SHOULD BE FIXED NOW")
# with open("blue2champWinRates2.pickle", 'wb') as pick:
#     pickle.dump(blue2champWinRates, pick)
#
# for x in tqdm(range(len(matches))):
#     # try:
#     blue3champWinRates.append(matches.iloc[x:x + 1, :].apply(lambda x: getWinRatio(x['platformId'], x['participantIdentities'][2]['player']['summonerName'], champ2champ[index2champ[x['participants'][2]['championId']]]), axis = 1))
#     # except Exception as e:
#     #     print("Index: ", x, " with exception: ", e)
#     #     time.sleep(125)
#     #     blue1champWinRates.append(matches.iloc[x:x + 1, :].apply(
#     #         lambda x: getWinRatio(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
#     #                               x['Blue Side Player 1 Champion']), axis = 1))
#     #     print("SHOULD BE FIXED NOW")
# with open("blue3champWinRates2.pickle", 'wb') as pick:
#     pickle.dump(blue3champWinRates, pick)
#
# for x in tqdm(range(len(matches))):
#     # try:
#     blue4champWinRates.append(matches.iloc[x:x + 1, :].apply(
#         lambda x: getWinRatio(x['platformId'], x['participantIdentities'][3]['player']['summonerName'],
#                               champ2champ[index2champ[x['participants'][3]['championId']]]), axis=1))
#     # except Exception as e:
#     #     print("Index: ", x, " with exception: ", e)
#     #     time.sleep(125)
#     #     blue1champWinRates.append(matches.iloc[x:x + 1, :].apply(
#     #         lambda x: getWinRatio(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
#     #                               x['Blue Side Player 1 Champion']), axis = 1))
#     #     print("SHOULD BE FIXED NOW")
# with open("blue4champWinRates2.pickle", 'wb') as pick:
#     pickle.dump(blue4champWinRates, pick)
#
# for x in tqdm(range(len(matches))):
#     # try:
#     blue5champWinRates.append(matches.iloc[x:x + 1, :].apply(
#         lambda x: getWinRatio(x['platformId'], x['participantIdentities'][4]['player']['summonerName'],
#                               champ2champ[index2champ[x['participants'][4]['championId']]]), axis=1))
#     # except Exception as e:
#     #     print("Index: ", x, " with exception: ", e)
#     #     time.sleep(125)
#     #     blue1champWinRates.append(matches.iloc[x:x + 1, :].apply(
#     #         lambda x: getWinRatio(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
#     #                               x['Blue Side Player 1 Champion']), axis = 1))
#     #     print("SHOULD BE FIXED NOW")
# with open("blue5champWinRates2.pickle", 'wb') as pick:
#     pickle.dump(blue5champWinRates, pick)
#
# for x in tqdm(range(len(matches))):
#     # try:
#     red1champWinRates.append(matches.iloc[x:x + 1, :].apply(
#         lambda x: getWinRatio(x['platformId'], x['participantIdentities'][5]['player']['summonerName'],
#                               champ2champ[index2champ[x['participants'][5]['championId']]]), axis=1))
#     # except Exception as e:
#     #     print("Index: ", x, " with exception: ", e)
#     #     time.sleep(125)
#     #     blue1champWinRates.append(matches.iloc[x:x + 1, :].apply(
#     #         lambda x: getWinRatio(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
#     #                               x['Blue Side Player 1 Champion']), axis = 1))
#     #     print("SHOULD BE FIXED NOW")
# with open("red1champWinRates2.pickle", 'wb') as pick:
#     pickle.dump(red1champWinRates, pick)
#
# for x in tqdm(range(len(matches))):
#     # try:
#     red2champWinRates.append(matches.iloc[x:x + 1, :].apply(
#         lambda x: getWinRatio(x['platformId'], x['participantIdentities'][6]['player']['summonerName'],
#                               champ2champ[index2champ[x['participants'][6]['championId']]]), axis=1))
#     # except Exception as e:
#     #     print("Index: ", x, " with exception: ", e)
#     #     time.sleep(125)
#     #     blue1champWinRates.append(matches.iloc[x:x + 1, :].apply(
#     #         lambda x: getWinRatio(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
#     #                               x['Blue Side Player 1 Champion']), axis = 1))
#     #     print("SHOULD BE FIXED NOW")
# with open("red2champWinRates2.pickle", 'wb') as pick:
#     pickle.dump(red2champWinRates, pick)
#
# for x in tqdm(range(len(matches))):
#     # try:
#     red3champWinRates.append(matches.iloc[x:x + 1, :].apply(
#         lambda x: getWinRatio(x['platformId'], x['participantIdentities'][7]['player']['summonerName'],
#                               champ2champ[index2champ[x['participants'][7]['championId']]]), axis=1))
#     # except Exception as e:
#     #     print("Index: ", x, " with exception: ", e)
#     #     time.sleep(125)
#     #     blue1champWinRates.append(matches.iloc[x:x + 1, :].apply(
#     #         lambda x: getWinRatio(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
#     #                               x['Blue Side Player 1 Champion']), axis = 1))
#     #     print("SHOULD BE FIXED NOW")
# with open("red3champWinRates2.pickle", 'wb') as pick:
#     pickle.dump(red3champWinRates, pick)
#
# for x in tqdm(range(len(matches))):
#     # try:
#     red4champWinRates.append(matches.iloc[x:x + 1, :].apply(
#         lambda x: getWinRatio(x['platformId'], x['participantIdentities'][8]['player']['summonerName'],
#                               champ2champ[index2champ[x['participants'][8]['championId']]]), axis=1))
#     # except Exception as e:
#     #     print("Index: ", x, " with exception: ", e)
#     #     time.sleep(125)
#     #     blue1champWinRates.append(matches.iloc[x:x + 1, :].apply(
#     #         lambda x: getWinRatio(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
#     #                               x['Blue Side Player 1 Champion']), axis = 1))
#     #     print("SHOULD BE FIXED NOW")
# with open("red4champWinRates2.pickle", 'wb') as pick:
#     pickle.dump(red4champWinRates, pick)
#
# for x in tqdm(range(len(matches))):
#     # try:
#     red5champWinRates.append(matches.iloc[x:x + 1, :].apply(
#         lambda x: getWinRatio(x['platformId'], x['participantIdentities'][9]['player']['summonerName'],
#                               champ2champ[index2champ[x['participants'][9]['championId']]]), axis=1))
#     # except Exception as e:
#     #     print("Index: ", x, " with exception: ", e)
#     #     time.sleep(125)
#     #     blue1champWinRates.append(matches.iloc[x:x + 1, :].apply(
#     #         lambda x: getWinRatio(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
#     #                               x['Blue Side Player 1 Champion']), axis = 1))
#     #     print("SHOULD BE FIXED NOW")
# with open("red5champWinRates2.pickle", 'wb') as pick:
#     pickle.dump(red5champWinRates, pick)

#
# ########################################################################################################################3
#
# for x in tqdm(range(len(matches))):
#     # try:
#     blue1champMatches.append(matches.iloc[x:x + 1, :].apply(lambda x: getChampGames(x['platformId'], x['participantIdentities'][0]['player']['summonerName'], champ2champ[index2champ[x['participants'][0]['championId']]]), axis = 1))
#     # except Exception as e:
#     #     print("Index: ", x, " with exception: ", e)
#     #     time.sleep(125)
#     #     blue1champWinRates.append(matches.iloc[x:x + 1, :].apply(
#     #         lambda x: getChampGames(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
#     #                               x['Blue Side Player 1 Champion']), axis = 1))
#     #     print("SHOULD BE FIXED NOW")
# with open("blue1champMatches.pickle", 'wb') as pick:
#     pickle.dump(blue1champMatches, pick)
#
# for x in tqdm(range(len(matches))):
#     # try:
#     blue2champMatches.append(matches.iloc[x:x + 1, :].apply(lambda x: getChampGames(x['platformId'], x['participantIdentities'][1]['player']['summonerName'], champ2champ[index2champ[x['participants'][1]['championId']]]), axis = 1))
#     # except Exception as e:
#     #     print("Index: ", x, " with exception: ", e)
#     #     time.sleep(125)
#     #     blue1champWinRates.append(matches.iloc[x:x + 1, :].apply(
#     #         lambda x: getChampGames(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
#     #                               x['Blue Side Player 1 Champion']), axis = 1))
#     #     print("SHOULD BE FIXED NOW")
# with open("blue2champMatches.pickle", 'wb') as pick:
#     pickle.dump(blue2champMatches, pick)
#
# for x in tqdm(range(len(matches))):
#     # try:
#     blue3champMatches.append(matches.iloc[x:x + 1, :].apply(lambda x: getChampGames(x['platformId'], x['participantIdentities'][2]['player']['summonerName'], champ2champ[index2champ[x['participants'][2]['championId']]]), axis = 1))
#     # except Exception as e:
#     #     print("Index: ", x, " with exception: ", e)
#     #     time.sleep(125)
#     #     blue1champMatches.append(matches.iloc[x:x + 1, :].apply(
#     #         lambda x: getChampGames(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
#     #                               x['Blue Side Player 1 Champion']), axis = 1))
#     #     print("SHOULD BE FIXED NOW")
# with open("blue3champMatches.pickle", 'wb') as pick:
#     pickle.dump(blue3champMatches, pick)
#
# for x in tqdm(range(len(matches))):
#     # try:
#     blue4champMatches.append(matches.iloc[x:x + 1, :].apply(
#         lambda x: getChampGames(x['platformId'], x['participantIdentities'][3]['player']['summonerName'],
#                               champ2champ[index2champ[x['participants'][3]['championId']]]), axis=1))
#     # except Exception as e:
#     #     print("Index: ", x, " with exception: ", e)
#     #     time.sleep(125)
#     #     blue1champMatches.append(matches.iloc[x:x + 1, :].apply(
#     #         lambda x: getChampGames(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
#     #                               x['Blue Side Player 1 Champion']), axis = 1))
#     #     print("SHOULD BE FIXED NOW")
# with open("blue4champMatches.pickle", 'wb') as pick:
#     pickle.dump(blue4champMatches, pick)
#
# for x in tqdm(range(len(matches))):
#     # try:
#     blue5champMatches.append(matches.iloc[x:x + 1, :].apply(
#         lambda x: getChampGames(x['platformId'], x['participantIdentities'][4]['player']['summonerName'],
#                               champ2champ[index2champ[x['participants'][4]['championId']]]), axis=1))
#     # except Exception as e:
#     #     print("Index: ", x, " with exception: ", e)
#     #     time.sleep(125)
#     #     blue1champMatches.append(matches.iloc[x:x + 1, :].apply(
#     #         lambda x: getChampGames(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
#     #                               x['Blue Side Player 1 Champion']), axis = 1))
#     #     print("SHOULD BE FIXED NOW")
# with open("blue5champMatches.pickle", 'wb') as pick:
#     pickle.dump(blue5champMatches, pick)
#
# for x in tqdm(range(len(matches))):
#     # try:
#     red1champMatches.append(matches.iloc[x:x + 1, :].apply(
#         lambda x: getChampGames(x['platformId'], x['participantIdentities'][5]['player']['summonerName'],
#                               champ2champ[index2champ[x['participants'][5]['championId']]]), axis=1))
#     # except Exception as e:
#     #     print("Index: ", x, " with exception: ", e)
#     #     time.sleep(125)
#     #     blue1champMatches.append(matches.iloc[x:x + 1, :].apply(
#     #         lambda x: getChampGames(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
#     #                               x['Blue Side Player 1 Champion']), axis = 1))
#     #     print("SHOULD BE FIXED NOW")
# with open("red1champMatches.pickle", 'wb') as pick:
#     pickle.dump(red1champMatches, pick)

for x in tqdm(range(len(matches))):
    # try:
    red2champMatches.append(matches.iloc[x:x + 1, :].apply(
        lambda x: getChampGames(x['platformId'], x['participantIdentities'][6]['player']['summonerName'],
                              champ2champ[index2champ[x['participants'][6]['championId']]]), axis=1))
    # except Exception as e:
    #     print("Index: ", x, " with exception: ", e)
    #     time.sleep(125)
    #     blue1champMatches.append(matches.iloc[x:x + 1, :].apply(
    #         lambda x: getChampGames(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
    #                               x['Blue Side Player 1 Champion']), axis = 1))
    #     print("SHOULD BE FIXED NOW")
with open("red2champMatches.pickle", 'wb') as pick:
    pickle.dump(red2champMatches, pick)

for x in tqdm(range(len(matches))):
    # try:
    red3champMatches.append(matches.iloc[x:x + 1, :].apply(
        lambda x: getChampGames(x['platformId'], x['participantIdentities'][7]['player']['summonerName'],
                              champ2champ[index2champ[x['participants'][7]['championId']]]), axis=1))
    # except Exception as e:
    #     print("Index: ", x, " with exception: ", e)
    #     time.sleep(125)
    #     blue1champMatches.append(matches.iloc[x:x + 1, :].apply(
    #         lambda x: getChampGames(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
    #                               x['Blue Side Player 1 Champion']), axis = 1))
    #     print("SHOULD BE FIXED NOW")
with open("red3champMatches.pickle", 'wb') as pick:
    pickle.dump(red3champMatches, pick)

for x in tqdm(range(len(matches))):
    # try:
    red4champMatches.append(matches.iloc[x:x + 1, :].apply(
        lambda x: getChampGames(x['platformId'], x['participantIdentities'][8]['player']['summonerName'],
                              champ2champ[index2champ[x['participants'][8]['championId']]]), axis=1))
    # except Exception as e:
    #     print("Index: ", x, " with exception: ", e)
    #     time.sleep(125)
    #     blue1champMatches.append(matches.iloc[x:x + 1, :].apply(
    #         lambda x: getChampGames(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
    #                               x['Blue Side Player 1 Champion']), axis = 1))
    #     print("SHOULD BE FIXED NOW")
with open("red4champMatches.pickle", 'wb') as pick:
    pickle.dump(red4champMatches, pick)

for x in tqdm(range(len(matches))):
    # try:
    red5champMatches.append(matches.iloc[x:x + 1, :].apply(
        lambda x: getChampGames(x['platformId'], x['participantIdentities'][9]['player']['summonerName'],
                              champ2champ[index2champ[x['participants'][9]['championId']]]), axis=1))
    # except Exception as e:
    #     print("Index: ", x, " with exception: ", e)
    #     time.sleep(125)
    #     blue1champMatches.append(matches.iloc[x:x + 1, :].apply(
    #         lambda x: getChampGames(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
    #                               x['Blue Side Player 1 Champion']), axis = 1))
    #     print("SHOULD BE FIXED NOW")
with open("red5champMatches.pickle", 'wb') as pick:
    pickle.dump(red5champMatches, pick)



#######################################################################################################################333

for x in tqdm(range(len(matches))):
    # try:
    blue1champKDA.append(matches.iloc[x:x + 1, :].apply(lambda x: getChampKDA(x['platformId'], x['participantIdentities'][0]['player']['summonerName'], champ2champ[index2champ[x['participants'][0]['championId']]]), axis = 1))
    # except Exception as e:
    #     print("Index: ", x, " with exception: ", e)
    #     time.sleep(125)
    #     blue1champKDA.append(matches.iloc[x:x + 1, :].apply(
    #         lambda x: getChampKDA(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
    #                               x['Blue Side Player 1 Champion']), axis = 1))
    #     print("SHOULD BE FIXED NOW")
with open("blue1champKDA.pickle", 'wb') as pick:
    pickle.dump(blue1champKDA, pick)

for x in tqdm(range(len(matches))):
    # try:
    blue2champKDA.append(matches.iloc[x:x + 1, :].apply(lambda x: getChampKDA(x['platformId'], x['participantIdentities'][1]['player']['summonerName'], champ2champ[index2champ[x['participants'][1]['championId']]]), axis = 1))
    # except Exception as e:
    #     print("Index: ", x, " with exception: ", e)
    #     time.sleep(125)
    #     blue1champKDA.append(matches.iloc[x:x + 1, :].apply(
    #         lambda x: getChampKDA(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
    #                               x['Blue Side Player 1 Champion']), axis = 1))
    #     print("SHOULD BE FIXED NOW")
with open("blue2champKDA.pickle", 'wb') as pick:
    pickle.dump(blue2champKDA, pick)

for x in tqdm(range(len(matches))):
    # try:
    blue3champKDA.append(matches.iloc[x:x + 1, :].apply(lambda x: getChampKDA(x['platformId'], x['participantIdentities'][2]['player']['summonerName'], champ2champ[index2champ[x['participants'][2]['championId']]]), axis = 1))
    # except Exception as e:
    #     print("Index: ", x, " with exception: ", e)
    #     time.sleep(125)
    #     blue1champKDA.append(matches.iloc[x:x + 1, :].apply(
    #         lambda x: getChampKDA(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
    #                               x['Blue Side Player 1 Champion']), axis = 1))
    #     print("SHOULD BE FIXED NOW")
with open("blue3champKDA.pickle", 'wb') as pick:
    pickle.dump(blue3champKDA, pick)

for x in tqdm(range(len(matches))):
    # try:
    blue4champKDA.append(matches.iloc[x:x + 1, :].apply(
        lambda x: getChampKDA(x['platformId'], x['participantIdentities'][3]['player']['summonerName'],
                              champ2champ[index2champ[x['participants'][3]['championId']]]), axis=1))
    # except Exception as e:
    #     print("Index: ", x, " with exception: ", e)
    #     time.sleep(125)
    #     blue1champKDA.append(matches.iloc[x:x + 1, :].apply(
    #         lambda x: getChampKDA(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
    #                               x['Blue Side Player 1 Champion']), axis = 1))
    #     print("SHOULD BE FIXED NOW")
with open("blue4champKDA.pickle", 'wb') as pick:
    pickle.dump(blue4champKDA, pick)

for x in tqdm(range(len(matches))):
    # try:
    blue5champKDA.append(matches.iloc[x:x + 1, :].apply(
        lambda x: getChampKDA(x['platformId'], x['participantIdentities'][4]['player']['summonerName'],
                              champ2champ[index2champ[x['participants'][4]['championId']]]), axis=1))
    # except Exception as e:
    #     print("Index: ", x, " with exception: ", e)
    #     time.sleep(125)
    #     blue1champKDA.append(matches.iloc[x:x + 1, :].apply(
    #         lambda x: getChampKDA(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
    #                               x['Blue Side Player 1 Champion']), axis = 1))
    #     print("SHOULD BE FIXED NOW")
with open("blue5champKDA.pickle", 'wb') as pick:
    pickle.dump(blue5champKDA, pick)

for x in tqdm(range(len(matches))):
    # try:
    red1champKDA.append(matches.iloc[x:x + 1, :].apply(
        lambda x: getChampKDA(x['platformId'], x['participantIdentities'][5]['player']['summonerName'],
                              champ2champ[index2champ[x['participants'][5]['championId']]]), axis=1))
    # except Exception as e:
    #     print("Index: ", x, " with exception: ", e)
    #     time.sleep(125)
    #     blue1champKDA.append(matches.iloc[x:x + 1, :].apply(
    #         lambda x: getChampKDA(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
    #                               x['Blue Side Player 1 Champion']), axis = 1))
    #     print("SHOULD BE FIXED NOW")
with open("red1champKDA.pickle", 'wb') as pick:
    pickle.dump(red1champKDA, pick)

for x in tqdm(range(len(matches))):
    # try:
    red2champKDA.append(matches.iloc[x:x + 1, :].apply(
        lambda x: getChampKDA(x['platformId'], x['participantIdentities'][6]['player']['summonerName'],
                              champ2champ[index2champ[x['participants'][6]['championId']]]), axis=1))
    # except Exception as e:
    #     print("Index: ", x, " with exception: ", e)
    #     time.sleep(125)
    #     blue1champKDA.append(matches.iloc[x:x + 1, :].apply(
    #         lambda x: getChampKDA(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
    #                               x['Blue Side Player 1 Champion']), axis = 1))
    #     print("SHOULD BE FIXED NOW")
with open("red2champKDA.pickle", 'wb') as pick:
    pickle.dump(red2champKDA, pick)

for x in tqdm(range(len(matches))):
    # try:
    red3champKDA.append(matches.iloc[x:x + 1, :].apply(
        lambda x: getChampKDA(x['platformId'], x['participantIdentities'][7]['player']['summonerName'],
                              champ2champ[index2champ[x['participants'][7]['championId']]]), axis=1))
    # except Exception as e:
    #     print("Index: ", x, " with exception: ", e)
    #     time.sleep(125)
    #     blue1champKDA.append(matches.iloc[x:x + 1, :].apply(
    #         lambda x: getChampKDA(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
    #                               x['Blue Side Player 1 Champion']), axis = 1))
    #     print("SHOULD BE FIXED NOW")
with open("red3champKDA.pickle", 'wb') as pick:
    pickle.dump(red3champKDA, pick)

for x in tqdm(range(len(matches))):
    # try:
    red4champKDA.append(matches.iloc[x:x + 1, :].apply(
        lambda x: getChampKDA(x['platformId'], x['participantIdentities'][8]['player']['summonerName'],
                              champ2champ[index2champ[x['participants'][8]['championId']]]), axis=1))
    # except Exception as e:
    #     print("Index: ", x, " with exception: ", e)
    #     time.sleep(125)
    #     blue1champKDA.append(matches.iloc[x:x + 1, :].apply(
    #         lambda x: getChampKDA(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
    #                               x['Blue Side Player 1 Champion']), axis = 1))
    #     print("SHOULD BE FIXED NOW")
with open("red4champKDA.pickle", 'wb') as pick:
    pickle.dump(red4champKDA, pick)

for x in tqdm(range(len(matches))):
    # try:
    red5champKDA.append(matches.iloc[x:x + 1, :].apply(
        lambda x: getChampKDA(x['platformId'], x['participantIdentities'][9]['player']['summonerName'],
                              champ2champ[index2champ[x['participants'][9]['championId']]]), axis=1))
    # except Exception as e:
    #     print("Index: ", x, " with exception: ", e)
    #     time.sleep(125)
    #     blue1champKDA.append(matches.iloc[x:x + 1, :].apply(
    #         lambda x: getChampKDA(x['platformId'], x['participantIdentities'][0]['player']['summonerName'],
    #                               x['Blue Side Player 1 Champion']), axis = 1))
    #     print("SHOULD BE FIXED NOW")
with open("red5champKDA.pickle", 'wb') as pick:
    pickle.dump(red5champKDA, pick)





