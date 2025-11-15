# lolanalyzer - Backend
Replay Tool Analyzer

## Features

### Find Champion Games
Find all games where a player played a specific champion from their latest 20 matches. Automatically saves both match logs and timeline data to a champion-specific folder.

## Setup

1. Install dependencies:
```bash
pip install requests python-dotenv
```

2. Create a `.env` file in the backend directory with your Riot API credentials:
```
RIOT_API_KEY=your_riot_api_key_here
PUUID=your_puuid_here  # Optional, can use Riot ID instead
```

## Usage

### Basic Usage

Run the main script:
```bash
python find_champion_games.py
```

The script will:
1. Search through the latest 20 games for the specified champion
2. Create a folder named after the champion (e.g., `lillia/`)
3. Save each match's log as `{match_id}_log.json`
4. Save each match's timeline as `{match_id}_timeline.json`

### Using as a Module

You can also import and use the functions in your own code:

```python
from find_champion_games import get_puuid_from_riot_id, find_champion_games

# Option 1: Using Riot ID
puuid = get_puuid_from_riot_id("PlayerName", "EUW")

# Option 2: Using PUUID directly
puuid = "your-puuid-here"

# Find all games with a specific champion (saves to folder automatically)
champion_games = find_champion_games(puuid, "Ashe", save_to_folder=True)

# Access match data
for game in champion_games:
    print(f"Match ID: {game['match_id']}")
    print(f"KDA: {game['player_stats']['kills']}/{game['player_stats']['deaths']}/{game['player_stats']['assists']}")
    print(f"Win: {game['player_stats']['win']}")
    # Timeline data is also available
    print(f"Timeline: {game['timeline_data'] is not None}")
```

See `example_usage.py` for more detailed examples.

## API Functions

### `get_puuid_from_riot_id(game_name: str, tag_line: str) -> Optional[str]`
Get a player's PUUID from their Riot ID (game name + tag line).

**Parameters:**
- `game_name`: The player's game name (e.g., "Player")
- `tag_line`: The player's tag line (e.g., "EUW")

**Returns:** PUUID string or None if not found

### `get_match_ids(puuid: str, count: int = 20) -> List[str]`
Get the latest match IDs for a player.

**Parameters:**
- `puuid`: The player's PUUID
- `count`: Number of matches to retrieve (default: 20)

**Returns:** List of match IDs

### `get_match_data(match_id: str) -> Optional[Dict]`
Get detailed match data for a specific match ID.

**Parameters:**
- `match_id`: The match ID

**Returns:** Match data dictionary or None if error

### `get_match_timeline(match_id: str) -> Optional[Dict]`
Get timeline data for a specific match ID.

**Parameters:**
- `match_id`: The match ID

**Returns:** Match timeline dictionary or None if error

### `find_champion_games(puuid: str, champion_name: str, save_to_folder: bool = True) -> List[Dict]`
Find all games where a player played a specific champion in their latest 20 games.

**Parameters:**
- `puuid`: The player's PUUID
- `champion_name`: The champion name to search for (case-insensitive)
- `save_to_folder`: If True (default), saves match logs and timelines to champion-specific folder

**Returns:** List of match data dictionaries with structure:
```python
{
    "match_id": str,
    "match_data": dict,      # Full match data from Riot API
    "timeline_data": dict,   # Match timeline data
    "player_stats": dict     # Player's stats for that match
}
```

**Folder Structure:**
When `save_to_folder=True`, creates:
```
champion_name/
  ├── {match_id}_log.json       # Match data
  └── {match_id}_timeline.json  # Timeline data
```

## Test Files

The `test_files/` directory contains examples of:
- Getting match IDs
- Fetching match logs
- Fetching match timelines
- Sample match data (JSON)
