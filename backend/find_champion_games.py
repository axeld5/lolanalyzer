"""
Script to find all games where a player played a specific champion
from their latest 20 games.
"""
import requests
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
import json
from pathlib import Path

load_dotenv()

RIOT_API_KEY = os.getenv("RIOT_API_KEY")

# Riot API endpoints
REGION = "europe"  # Europe routing value
PLATFORM = "euw1"  # Platform for account lookup


def get_puuid_from_riot_id(game_name: str, tag_line: str) -> Optional[str]:
    """
    Get PUUID from Riot ID (game name + tag line).
    
    Args:
        game_name: The player's game name (e.g., "Player")
        tag_line: The player's tag line (e.g., "EUW")
    
    Returns:
        PUUID string or None if not found
    """
    url = f"https://{REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    params = {"api_key": RIOT_API_KEY}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("puuid")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching PUUID: {e}")
        return None


def get_match_ids(puuid: str, count: int = 20) -> List[str]:
    """
    Get the latest match IDs for a player.
    
    Args:
        puuid: The player's PUUID
        count: Number of matches to retrieve (default: 20)
    
    Returns:
        List of match IDs
    """
    url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
    params = {
        "api_key": RIOT_API_KEY,
        "count": count
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching match IDs: {e}")
        return []


def get_match_data(match_id: str) -> Optional[Dict]:
    """
    Get detailed match data for a specific match ID.
    
    Args:
        match_id: The match ID
    
    Returns:
        Match data dictionary or None if error
    """
    url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    params = {"api_key": RIOT_API_KEY}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching match data for {match_id}: {e}")
        return None


def get_match_timeline(match_id: str) -> Optional[Dict]:
    """
    Get timeline data for a specific match ID.
    
    Args:
        match_id: The match ID
    
    Returns:
        Match timeline dictionary or None if error
    """
    url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
    params = {"api_key": RIOT_API_KEY}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching timeline for {match_id}: {e}")
        return None


def find_champion_games(puuid: str, champion_name: str, save_to_folder: bool = True) -> List[Dict]:
    """
    Find all games where a player played a specific champion in their latest 20 games.
    
    Args:
        puuid: The player's PUUID
        champion_name: The champion name to search for (case-insensitive)
        save_to_folder: If True, saves match data and timeline to champion-specific folder
    
    Returns:
        List of match data dictionaries where the player played the specified champion
    """
    print(f"Fetching latest 20 match IDs for player...")
    match_ids = get_match_ids(puuid, count=20)
    
    if not match_ids:
        print("No match IDs found.")
        return []
    
    print(f"Found {len(match_ids)} matches. Filtering for {champion_name} games...")
    
    # Create champion folder if saving
    champion_folder = None
    if save_to_folder:
        champion_folder_name = champion_name.lower().replace(" ", "_").replace("'", "")
        champion_folder = Path(champion_folder_name)
        champion_folder.mkdir(exist_ok=True)
        print(f"Saving data to folder: {champion_folder}/")
    
    champion_games = []
    champion_name_lower = champion_name.lower().replace(" ", "").replace("'", "")
    
    for i, match_id in enumerate(match_ids, 1):
        print(f"Checking match {i}/{len(match_ids)}: {match_id}")
        match_data = get_match_data(match_id)
        
        if not match_data:
            continue
        
        # Find the player in the participants list
        participants = match_data.get("info", {}).get("participants", [])
        for participant in participants:
            if participant.get("puuid") == puuid:
                participant_champion = participant.get("championName", "").lower()
                
                if participant_champion == champion_name_lower:
                    print(f"  ✓ Found {champion_name} game!")
                    
                    # Get timeline data
                    print(f"  → Fetching timeline data...")
                    timeline_data = get_match_timeline(match_id)
                    
                    game_info = {
                        "match_id": match_id,
                        "match_data": match_data,
                        "timeline_data": timeline_data,
                        "player_stats": participant
                    }
                    
                    # Save to folder if requested
                    if save_to_folder and champion_folder:
                        # Save match log
                        log_file = champion_folder / f"{match_id}_log.json"
                        with open(log_file, 'w') as f:
                            json.dump(match_data, f, indent=4)
                        print(f"  → Saved match log to {log_file}")
                        
                        # Save timeline
                        if timeline_data:
                            timeline_file = champion_folder / f"{match_id}_timeline.json"
                            with open(timeline_file, 'w') as f:
                                json.dump(timeline_data, f, indent=4)
                            print(f"  → Saved timeline to {timeline_file}")
                    
                    champion_games.append(game_info)
                else:
                    print(f"  ✗ Played {participant.get('championName')} instead")
                break
    
    return champion_games


def main():
    """
    Main function to demonstrate usage.
    You can provide either PUUID directly or Riot ID (game name + tag).
    """
    # Option 1: Use PUUID from environment variable
    puuid = os.getenv("PUUID")
    
    # Option 2: Or use Riot ID to get PUUID
    # Uncomment these lines and set your game name and tag
    game_name = "IPlayToWin10"
    tag_line = "EUW"
    puuid = get_puuid_from_riot_id(game_name, tag_line)
    
    if not puuid:
        print("Error: No PUUID provided. Set PUUID in .env or use get_puuid_from_riot_id()")
        return
    
    # Specify the champion to search for
    champion_name = "Lillia"
    
    if not champion_name:
        print("Error: Champion name is required.")
        return
    
    # Find all games with the specified champion (saves to folder automatically)
    champion_games = find_champion_games(puuid, champion_name, save_to_folder=True)
    
    # Display results summary
    print("\n" + "="*60)
    print(f"RESULTS: Found {len(champion_games)} games with {champion_name}")
    print("="*60)
    
    champion_folder_name = champion_name.lower().replace(" ", "_").replace("'", "")
    
    for i, game in enumerate(champion_games, 1):
        player_stats = game["player_stats"]
        match_info = game["match_data"]["info"]
        
        print(f"\nGame {i}:")
        print(f"  Match ID: {game['match_id']}")
        print(f"  Champion: {player_stats.get('championName')}")
        print(f"  KDA: {player_stats.get('kills')}/{player_stats.get('deaths')}/{player_stats.get('assists')}")
        print(f"  Win: {player_stats.get('win')}")
        print(f"  Game Duration: {match_info.get('gameDuration')} seconds")
        print(f"  Game Mode: {match_info.get('gameMode')}")
    
    if champion_games:
        print(f"\n✓ All match logs and timelines saved to '{champion_folder_name}/' folder")
        print(f"  - {len(champion_games)} match logs (*_log.json)")
        print(f"  - {len(champion_games)} timelines (*_timeline.json)")


if __name__ == "__main__":
    main()

