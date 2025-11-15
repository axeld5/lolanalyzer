# lolanalyzer - Backend
Replay Tool Analyzer

## Features

### 1. Find Champion Games
Find all games where a player played a specific champion from their latest 20 matches. Automatically saves both match logs and timeline data to a champion-specific folder.

### 2. AI-Powered Match Analysis (Phase-Based)
Analyze match replays using a multi-stage Claude 4.5 Sonnet process:
- **Stage 1**: Extract game context and player statistics from match log
- **Stage 2-4**: Analyze each game phase separately (early, mid, late)
- **Stage 5**: Synthesize all phases into cohesive coaching review

This phase-based approach provides:
- **Better token efficiency**: Each phase analyzed separately (~50-120K tokens vs 300K+ full timeline)
- **More contextual coaching**: Phase-appropriate feedback (laning tips, teamfight analysis, late-game decisions)
- **Better game flow**: Each phase builds on previous ones for coherent narrative
- **Scalability**: Works for any game length (short games skip missing phases)

### 3. Audio Review Generation
Convert text analysis to natural-sounding audio using ElevenLabs text-to-speech, perfect for listening while you play or commute.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the backend directory with your API credentials:
```
# Riot Games API
RIOT_API_KEY=your_riot_api_key_here
PUUID=your_puuid_here  # Optional, can use Riot ID instead

# Claude AI (for match analysis)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# ElevenLabs (for audio generation)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

Get your API keys:
- Riot API: https://developer.riotgames.com/
- Anthropic: https://console.anthropic.com/
- ElevenLabs: https://elevenlabs.io/

## Usage

### Quick Start - Complete Pipeline

Generate an AI-analyzed audio review for your games:

```bash
# Using Riot ID
python main.py Lillia --game-name IPlayToWin10 --tag EUW

# Using PUUID from .env
python main.py Ashe

# With custom voice and output
python main.py "Lee Sin" --game-name Player --tag EUW --voice adam --output my_review.mp3
```

This will:
1. Fetch all games for the specified champion
2. **Stage 1**: Analyze match statistics for context
3. **Stage 2-4**: Analyze early, mid, and late game phases separately
4. **Stage 5**: Synthesize all phases into final coaching review
5. Generate audio review using ElevenLabs
6. Save everything to the champion folder

**Cost**: ~$0.20-0.25 per game analysis (5 Claude API calls with sparse JSON optimization)

### Individual Components

#### 1. Fetch Games Only

```bash
python find_champion_games.py
```

The script will:
1. Search through the latest 20 games for the specified champion
2. Create a folder named after the champion (e.g., `lillia/`)
3. Save each match's log as `{match_id}_log.json`
4. Save each match's timeline as `{match_id}_timeline.json`

#### 2. Analyze a Match

```bash
python make_analysis.py lillia/EUW1_123_log.json lillia/EUW1_123_timeline.json <puuid>
```

#### 3. Convert Analysis to Audio

```bash
python create_audio.py analysis.txt analysis.mp3 george
```

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

## Available Voices

Choose from these ElevenLabs voices:
- **george** (default) - Clear, professional
- **adam** - Deep, authoritative
- **bill** - Warm, friendly
- **callum** - Young, energetic
- **charlie** - British, natural

## Main Pipeline Options

```bash
python main.py CHAMPION [options]

Required:
  CHAMPION              Champion name (e.g., Lillia, Ashe, "Lee Sin")

Optional:
  --game-name NAME      Riot ID game name
  --tag TAG             Riot ID tag line (default: EUW)
  --puuid PUUID         Player PUUID (overrides game-name/tag)
  --voice VOICE         Voice for audio (default: george)
  --output FILE         Output audio file name
  --save-text           Also save analysis as text file
  --no-fetch            Skip fetching games (use existing folder)
```

## Examples

### Full Pipeline Examples

```bash
# Basic usage with Riot ID
python main.py Lillia --game-name IPlayToWin10 --tag EUW

# Using PUUID from .env file
python main.py Ashe

# Custom voice and save text analysis
python main.py Jinx --game-name Player --tag NA1 --voice adam --save-text

# Use existing data (no API fetch)
python main.py Lillia --no-fetch --voice charlie
```

### Individual Components

```bash
# 1. Only fetch games
python find_champion_games.py

# 2. Only analyze
python make_analysis.py lillia/EUW1_123_log.json lillia/EUW1_123_timeline.json <puuid>

# 3. Only create audio from existing analysis
python create_audio.py analysis.txt output.mp3 george
```

## Project Structure

```
backend/
├── main.py                      # Complete pipeline orchestrator
├── find_champion_games.py       # Game fetching with sparse JSON
├── split_timeline.py            # Phase splitting (early/mid/late)
├── prompt.py                    # Phase-based AI prompts
├── make_analysis.py             # Phase-based Claude AI analysis
├── make_json_efficient.py       # Sparse JSON optimization
├── create_audio.py              # ElevenLabs audio generation
├── requirements.txt             # Dependencies
├── README.md                    # This file
├── PHASE_BASED_ANALYSIS.md      # Phase-based architecture explanation
│
└── {champion_name}/             # Auto-created per champion
    ├── {match_id}_log.json              # Match data (~150KB)
    ├── {match_id}_timeline.json         # Full timeline (sparse, ~1.2MB)
    ├── {match_id}_timeline_early.json   # Early game phase (0-15 min)
    ├── {match_id}_timeline_mid.json     # Mid game phase (15-30 min)
    ├── {match_id}_timeline_late.json    # Late game phase (30+ min)
    ├── {match_id}_context.txt           # Stage 1 output (if --save-text)
    ├── {match_id}_analysis_early.txt    # Stage 2 output (if --save-text)
    ├── {match_id}_analysis_mid.txt      # Stage 3 output (if --save-text)
    ├── {match_id}_analysis_late.txt     # Stage 4 output (if --save-text)
    ├── {match_id}_analysis_final.txt    # Stage 5 output (if --save-text)
    └── {match_id}_analysis.mp3          # Audio review (from final synthesis)
```

## Phase-Based Analysis Architecture

The data files are massive and contain lots of redundant zeros:
- Match Log: ~3,700 lines (~150KB)
- Timeline (original): ~47,000 lines (~2MB) → **306K tokens!**
- Timeline (sparse): ~35,000 lines (~1.2MB) → **50% reduction**

**Phase-based approach:**
1. **Stage 1**: Analyze match log → Generate context summary
2. **Stage 2**: Analyze early game (0-15 min) → ~81K tokens
3. **Stage 3**: Analyze mid game (15-30 min) → ~117K tokens
4. **Stage 4**: Analyze late game (30+ min) → ~103K tokens
5. **Stage 5**: Synthesize all phases → Final coaching review

**Benefits:**
- ✅ Each phase fits comfortably in context (40-60% usage)
- ✅ Phase-specific coaching (laning tips, teamfight analysis, late-game decisions)
- ✅ Better narrative flow (each phase builds on previous)
- ✅ ~50% token reduction through sparse JSON
- ✅ Scalable for any game length
- ✅ More detailed analysis per phase

See `PHASE_BASED_ANALYSIS.md` for detailed explanation.

## Test Files

The `old_files/` directory contains legacy examples and test files.
