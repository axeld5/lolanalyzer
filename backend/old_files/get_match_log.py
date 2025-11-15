import requests
import os
from dotenv import load_dotenv

load_dotenv()

puuid = os.getenv("PUUID")
RIOT_API_KEY = os.getenv("RIOT_API_KEY")
url = f"https://europe.api.riotgames.com//lol/match/v5/matches/EUW1_7603668623?api_key={RIOT_API_KEY}"
data = requests.get(url).json()

import json

with open('match_log.json', 'w') as f:
    json.dump(data, f, indent=4)
