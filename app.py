from flask import Flask
from flask import render_template
from flask import url_for
import requests
from requests import get
import json
import pickle
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd
from flask_socketio import *
import time
import os


app = Flask(__name__)
socketio = SocketIO(app, logger=True)


@socketio.on('checkLive')
def checkLive():
    try:
        response = requests.get('https://127.0.0.1:2999/liveclientdata/allgamedata')
    except:
        if os.path.exists('variables2.pickle'):
            os.remove('variables2.pickle')
        pass


@app.route('/index')
@app.route('/<int:port>')
def predict(port):
    try:
        with open("variables2.pickle", "rb") as pick:
            variables = pickle.load(pick)
        return render_template('index.html', variables=variables)
    except Exception as e:
        try:
            print(e)
            print("A nee live match has started!")
            with open("rf.pickle", "rb") as pick:
                rf = pickle.load(pick)
            prediction_data, player_list = getData(port)

            prediction_data = pd.DataFrame(prediction_data, index=[0])
            prediction = rf.predict_proba(prediction_data)[0]
            variables = {}
            variables['predictionData'] = prediction_data
            variables['summonerList'] = player_list
            variables['predictions'] = prediction
            with open("variables2.pickle", "wb") as pick:
                pickle.dump(variables, pick)

            return render_template('index.html', variables=variables)
        except:
            return "No Ongoing Match Right now..."

@socketio.on('startMatch')
def startMatch():
    time.sleep(5)
    emit('redirect', {'url': url_for('predict')})

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

    return float(
        soup.find(text=currentChampion).parent.parent.parent.parent.find("td", {"class": "KDA"})['data-value'])

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
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)
    url = f"https://{region}op.gg/statistics/champion/"
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return soup.find(text=currentChampion).parent.parent.parent.findAll("td")[3]['data-value']


def getData(port):
    with open("item2value.pickle", "rb") as pick:
        item2value = pickle.load(pick)
    response = requests.get(f'https://127.0.0.1:{port}/liveclientdata/allgamedata')
    # with open("exjson.json", "rb") as pick:
    #     response = pickle.load(pick)
    text = json.loads(response)
    data = {}
    data['Blue Side Elders'] = 0
    data['Red Side Elders'] = 0
    data['Blue Side Dragon Kills'] = 0
    data['Red Side Dragon Kills'] = 0

    data['Blue Side RiftHerald Kills'] = 0
    data['Red Side RiftHerald Kills'] = 0

    data['Blue Side Towers Destroyed'] = 0
    data['Red Side Towers Destroyed'] = 0

    data['Blue Side Inhibitors Destroyed'] = 0
    data['Red Side Inhibitors Destroyed'] = 0

    data['Blue Side Baron Kills'] = 0
    data['Red Side Baron Kills'] = 0

    for event in text['events']['Events']:
        if event['EventName'] == 'DragonKill':
            if event['DragonType'] == "Elder":
                data['Blue Side Elders'] += 1 if \
                next(player for player in text['allPlayers'] if player['summonerName'] == event['KillerName'])[
                    'team'] == "ORDER" else 0
                data['Red Side Elders'] += 1 if \
                next(player for player in text['allPlayers'] if player['summonerName'] == event['KillerName'])[
                    'team'] != "ORDER" else 0
            else:
                data['Blue Side Dragon Kills'] += 1 if \
                next(player for player in text['allPlayers'] if player['summonerName'] == event['KillerName'])[
                    'team'] == "ORDER" else 0
                data['Red Side Dragon Kills'] += 1 if \
                next(player for player in text['allPlayers'] if player['summonerName'] == event['KillerName'])[
                    'team'] != "ORDER" else 0
            continue
        if event['EventName'] == 'HeraldKill':
            data['Blue Side RiftHerald Kills'] += 1 if \
            next(player for player in text['allPlayers'] if player['summonerName'] == event['KillerName'])[
                'team'] == "ORDER" else 0
            data['Red Side RiftHerald Kills'] += 1 if \
            next(player for player in text['allPlayers'] if player['summonerName'] == event['KillerName'])[
                'team'] != "ORDER" else 0
            continue
        if event['EventName'] == 'TurretKilled':
            data['Blue Side Towers Destroyed'] += 1 if \
            next(player for player in text['allPlayers'] if player['summonerName'] == event['KillerName'])[
                'team'] != "ORDER" else 0
            data['Red Side Towers Destroyed'] += 1 if \
            next(player for player in text['allPlayers'] if player['summonerName'] == event['KillerName'])[
                'team'] == "ORDER" else 0
            continue
        if event['EventName'] == "InhibKilled":
            data['Blue Side Inhibitors Destroyed'] += 1 if \
            next(player for player in text['allPlayers'] if player['summonerName'] == event['KillerName'])[
                'team'] != "ORDER" else 0
            data['Red Side Inhibitors Destroyed'] += 1 if \
            next(player for player in text['allPlayers'] if player['summonerName'] == event['KillerName'])[
                'team'] == "ORDER" else 0
            continue
        if event['EventName'] == 'BaronKill':
            data['Blue Side Baron Kills'] += 1 if \
            next(player for player in text['allPlayers'] if player['summonerName'] == event['KillerName'])[
                'team'] == "ORDER" else 0
            data['Red Side Baron Kills'] += 1 if \
            next(player for player in text['allPlayers'] if player['summonerName'] == event['KillerName'])[
                'team'] != "ORDER" else 0

    player_list = {}
    for info, player in zip(text['allPlayers'],
                            ['Blue Side Player 1', 'Blue Side Player 2', 'Blue Side Player 3', 'Blue Side Player 4',
                             'Blue Side Player 5', 'Red Side Player 1', 'Red Side Player 2', 'Red Side Player 3',
                             'Red Side Player 4', 'Red Side Player 5']):
        player_list[player + ' Name'] = info['summonerName']
        data[player + ' Kills'] = info['scores']['kills']
        data[player + ' Deaths'] = info['scores']['deaths']
        data[player + ' Assists'] = info['scores']['assists']
        data[player + ' Champ Level'] = info['level']
        data[player + ' Vision Score'] = info['scores']['wardScore']
        data[player + ' Power Level'] = 0
        for item in info['items']:
            data[player + ' Power Level'] += item2value[item['displayName']]
        try:
            data[player + ' Champ WinRate'] = getChampWinRate("NA1", info['championName'])
        except Exception as e:
            print(e)
            data[player + ' Champ WinRate'] = 50
        try:
            data[player + ' Champ Matches'] = getChampGames("NA1", info['summonerName'], info['championName'])
        except Exception as e:
            print(e)
            data[player + ' Champ Matches'] = 0
        try:
            data[player + ' Champ KDA'] = getChampKDA("NA1", info['summonerName'], info['championName'])
        except Exception as e:
            print(e)
            data[player + ' Champ KDA'] = 2.2

    data['Blue Side Total Power Level'] = data['Blue Side Player 1 Power Level'] + data[
        'Blue Side Player 2 Power Level'] + data['Blue Side Player 3 Power Level'] + data[
                                              'Blue Side Player 4 Power Level'] + data['Blue Side Player 5 Power Level']
    data['Red Side Total Power Level'] = data['Red Side Player 1 Power Level'] + data['Red Side Player 2 Power Level'] + \
                                         data['Red Side Player 3 Power Level'] + data['Red Side Player 4 Power Level'] + \
                                         data['Red Side Player 5 Power Level']

    data['Blue Side Power Level Difference'] = data['Blue Side Total Power Level'] - data['Red Side Total Power Level']

    data['Blue Side Total Vision Score'] = data['Blue Side Player 1 Vision Score'] + data[
        'Blue Side Player 2 Vision Score'] + data['Blue Side Player 3 Vision Score'] + data[
                                               'Blue Side Player 4 Vision Score'] + data[
                                               'Blue Side Player 5 Vision Score']
    data['Red Side Total Vision Score'] = data['Red Side Player 1 Vision Score'] + data[
        'Red Side Player 2 Vision Score'] + data['Red Side Player 3 Vision Score'] + data[
                                              'Red Side Player 4 Vision Score'] + data['Red Side Player 5 Vision Score']

    data['Blue Side Vision Score Difference'] = data['Blue Side Total Vision Score'] - data[
        'Red Side Total Vision Score']

    data['Blue Side Total Kills'] = data['Blue Side Player 1 Kills'] + data['Blue Side Player 2 Kills'] + data[
        'Blue Side Player 3 Kills'] + data['Blue Side Player 4 Kills'] + data['Blue Side Player 5 Kills']
    data['Red Side Total Kills'] = data['Red Side Player 1 Kills'] + data['Red Side Player 2 Kills'] + data[
        'Red Side Player 3 Kills'] + data['Red Side Player 4 Kills'] + data['Red Side Player 5 Kills']

    data['Blue Side Kills Difference'] = data['Blue Side Total Kills'] - data['Red Side Total Kills']

    data['gameDuration'] = text['gameData']['gameTime']

    return data, player_list

if __name__ == '__main__':
    socketio.run(app, debug=False)

