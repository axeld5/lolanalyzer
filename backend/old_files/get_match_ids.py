import requests
import os
from dotenv import load_dotenv

load_dotenv()

puuid = os.getenv("PUUID")
RIOT_API_KEY = os.getenv("RIOT_API_KEY")
url = f"https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?api_key={RIOT_API_KEY}"
data = requests.get(url).json()
print(data)