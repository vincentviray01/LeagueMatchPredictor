import pandas as pd
import requests
from riotwatcher import LolWatcher, ApiError
import json


API_KEY = "RGAPI-2e65583b-4c32-4042-b831-0d0d7f720ae0"
PLATFORM_ROUTING_VALUE = "na1.api.riotgames.com"
REGIONAL_ROUTING_VALUE = "americas.api.riotgames.com"
watcher = LolWatcher(API_KEY)
region = 'na1'

if __name__ == "__main__":
    query = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/Doublelift?api_key=RGAPI-2e65583b-4c32-4042-b831-0d0d7f720ae0"
    response = requests.get(query)
    me = watcher.summoner.by_name(region, "One Random Enemy")

    my_ranked_stats = watcher.league.by_summoner(region, me['id'])
    print(json.dumps(me, indent=4))
    print(json.dumps(my_ranked_stats, indent = 4))

    df = pd.DataFrame()
    df.append(my_ranked_stats)
    print(df)
