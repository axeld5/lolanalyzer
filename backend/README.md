# lolanalyzer - Backend
Replay Tool Analyzer

## Features

### 1. Find Champion Games
Find all games where a player played a specific champion from their latest 20 matches. Automatically saves both match logs and timeline data to a champion-specific folder.

### 2. AI-Powered Match Analysis (Single-Pass)
Analyze match replays using Claude 4.5 Sonnet with extended context (1M tokens):
- **Single-Pass Analysis**: Processes entire match log + timeline in one comprehensive analysis
- **Extended Context**: Uses Claude's beta API with 1M token context window
- **Complete Game View**: Analyzes the full game flow from start to finish in one pass
- **Optimized Data**: Sparse JSON and delta encoding reduce token usage by 40-60%

**Alternative**: Phase-based analysis (early/mid/late) is still available as an option for more granular analysis.

### 3. Audio Review Generation
Convert text analysis to natural-sounding audio using ElevenLabs text-to-speech, perfect for listening while you play or commute.

### 4. Advanced Data Optimization
- **Team Side Detection**: All data includes Blue/Red team identification
- **Delta Encoding**: Frames show only changed stats in `"old → new"` format
- **Sparse JSON**: Automatically removes zeros, nulls, and empty values (~50% size reduction)
- **Token Efficiency**: Optimized data reduces AI analysis costs by 40-60%

## Setup

1. Install dependencies using `uv`:
```bash
# Create virtual environment and install dependencies
uv venv
uv sync

# Activate the virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows
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

### Docker Setup

Build and run the FastAPI backend using Docker:

```bash
# Build the Docker image
docker build -t lolanalyzer-backend .

# Run the container with environment variables
docker run -d \
  --name lolanalyzer-backend \
  -p 8000:8000 \
  -e RIOT_API_KEY=your_riot_api_key_here \
  -e ANTHROPIC_API_KEY=your_anthropic_api_key_here \
  -e ELEVENLABS_API_KEY=your_elevenlabs_api_key_here \
  -e PUUID=your_puuid_here \
  lolanalyzer-backend
```

Or use an `.env` file:

```bash
# Build the Docker image
docker build -t lolanalyzer-backend .

# Run with .env file
docker run -d \
  --name lolanalyzer-backend \
  -p 8000:8000 \
  --env-file .env \
  lolanalyzer-backend
```

The API will be available at `http://localhost:8000`

## Usage

### Running the FastAPI Server

Start the REST API server:

```bash
# Activate virtual environment first
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows

# Run the FastAPI server
uvicorn main_fastapi:app --host 0.0.0.0 --port 8000 --reload
```

Or using `uv`:
```bash
uv run uvicorn main_fastapi:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### 1. Fetch Champion Games
`POST /api/fetch-games`

Fetch all games where a player played a specific champion.

**Request:**
```json
{
  "game_name": "IPlayToWin10",
  "tag": "EUW",
  "champion": "Lillia"
}
```

**Response:**
```json
{
  "games": [
    {
      "id": "game_20251112_0Jsp",
      "match_id": "EUW1_1234567890",
      "champion": "Lillia",
      "result": "Victory",
      "kda": "12/3/8",
      "duration": "32:45",
      "date": "2025-11-12"
    }
  ],
  "champion": "Lillia",
  "puuid": "player-puuid-here"
}
```

#### 2. Analyze Games
`POST /api/analyze-games`

Analyze selected games and generate audio reviews.

**Request:**
```json
{
  "game_ids": ["game_20251112_0Jsp", "game_20251112_1hiz"],
  "champion": "Lillia",
  "puuid": "player-puuid-here",
  "voice": "george"
}
```

**Response:**
```json
{
  "gameAnalyses": [
    {
      "gameId": "game_20251112_0Jsp",
      "match_id": "EUW1_1234567890",
      "champion": "Lillia",
      "audioUrl": "/api/audio/lillia/game_20251112_0Jsp_analysis.mp3",
      "summary": "Great early game performance with strong jungle control...",
      "detailedAnalysis": "Full analysis text here...",
      "phaseAnalyses": null  # null for single-pass analysis, populated for phase-based
    }
  ],
  "globalAnalysisUrl": "/api/audio/lillia/Lillia_global_analysis.mp3",
  "globalSummary": "Overall performance summary...",
  "globalDetailedAnalysis": "Full global analysis..."
}
```

#### 3. Download Audio
`GET /api/audio/{champion}/{filename}`

Download generated audio files.

**Example:**
```
GET /api/audio/lillia/game_20251112_0Jsp_analysis.mp3
```

#### 4. Health Check
`GET /api/health`

Check if the API is running.

#### 5. Get Available Voices
`GET /api/voices`

Get list of available ElevenLabs voices.

**Cost**: ~$0.05-0.10 per game analysis (single Claude API call with extended context and sparse JSON optimization)

### Standalone Scripts (CLI)

The backend also provides standalone scripts for direct use:

#### 1. Fetch Games Only

```bash
python find_champion_games.py
```

The script will prompt for:
- Riot ID (game name and tag) or use PUUID from `.env`
- Champion name

It will:
1. Search through the latest 20 games for the specified champion
2. Create a folder named after the champion (e.g., `lillia/`)
3. Save each match's log as `game_YYYYMMDD_XXXX_log.json`
4. Save each match's timeline as `game_YYYYMMDD_XXXX_timeline.json`

#### 2. Analyze a Match

```bash
python make_analysis.py <log_file> <timeline_file> <player_puuid>
```

**Example:**
```bash
python make_analysis.py lillia/game_20251112_0Jsp_log.json lillia/game_20251112_0Jsp_timeline.json <puuid>
```

This will output:
- **Single-Pass Analysis**: Complete coaching review analyzing the entire game in one pass

**Note**: By default, uses single-pass analysis. To use phase-based analysis instead, modify the code to pass `use_single_pass=False` to `analyze_match_async()`.

#### 3. Convert Analysis to Audio

```bash
python create_audio.py <text_file> <output_file> <voice>
```

**Example:**
```bash
python create_audio.py analysis.txt analysis.mp3 george
```

### Using as a Module

You can also import and use the functions in your own Python code:

```python
from find_champion_games import get_puuid_from_riot_id, find_champion_games
from make_analysis import analyze_match_async
from create_audio import text_to_speech, get_voice_id

# Get PUUID from Riot ID
puuid = get_puuid_from_riot_id("PlayerName", "EUW")

# Find all games with a specific champion (saves to folder automatically)
champion_games = find_champion_games(puuid, "Ashe", save_to_folder=True)

# Access match data
for game in champion_games:
    print(f"Match ID: {game['match_id']}")
    print(f"KDA: {game['player_stats']['kills']}/{game['player_stats']['deaths']}/{game['player_stats']['assists']}")
    print(f"Win: {game['player_stats']['win']}")
    # Timeline data is also available
    print(f"Timeline: {game['timeline_data'] is not None}")
    
    # Analyze a match (default: single-pass analysis)
    match_context, phase_analyses, final_review = await analyze_match_async(
        game['match_data'],
        game['timeline_data'],
        puuid,
        use_single_pass=True  # Default: True for single-pass, False for phase-based
    )
    
    # Note: For single-pass analysis, match_context and phase_analyses will be empty
    # The complete analysis is in final_review
    
    # Generate audio
    voice_id = get_voice_id("george")
    text_to_speech(final_review, "analysis.mp3", voice_id=voice_id)
```

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
  ├── game_YYYYMMDD_XXXX_log.json       # Match data (e.g., game_20251112_0Jsp_log.json)
  └── game_YYYYMMDD_XXXX_timeline.json  # Timeline data (e.g., game_20251112_0Jsp_timeline.json)
```

Where `YYYYMMDD` is the game date and `XXXX` is a 4-character random UID.

## Available Voices

Choose from these ElevenLabs voices (use with `voice` parameter in API requests):
- **george** (default) - Clear, professional
- **adam** - Deep, authoritative
- **bill** - Warm, friendly
- **callum** - Young, energetic
- **charlie** - British, natural

Get the full list via `GET /api/voices`

## API Examples

### Complete Workflow Example

```bash
# 1. Start the API server
uvicorn main_fastapi:app --host 0.0.0.0 --port 8000

# 2. Fetch games (using curl or your frontend)
curl -X POST http://localhost:8000/api/fetch-games \
  -H "Content-Type: application/json" \
  -d '{
    "game_name": "IPlayToWin10",
    "tag": "EUW",
    "champion": "Lillia"
  }'

# 3. Analyze selected games
curl -X POST http://localhost:8000/api/analyze-games \
  -H "Content-Type: application/json" \
  -d '{
    "game_ids": ["game_20251112_0Jsp", "game_20251112_1hiz"],
    "champion": "Lillia",
    "puuid": "player-puuid-from-fetch-response",
    "voice": "george"
  }'

# 4. Download audio
curl http://localhost:8000/api/audio/lillia/game_20251112_0Jsp_analysis.mp3 \
  --output analysis.mp3
```

### Using Python Requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Fetch games
response = requests.post(f"{BASE_URL}/api/fetch-games", json={
    "game_name": "IPlayToWin10",
    "tag": "EUW",
    "champion": "Lillia"
})
data = response.json()
puuid = data["puuid"]
game_ids = [game["id"] for game in data["games"]]

# Analyze games
response = requests.post(f"{BASE_URL}/api/analyze-games", json={
    "game_ids": game_ids[:2],  # Analyze first 2 games
    "champion": "Lillia",
    "puuid": puuid,
    "voice": "george"
})
analyses = response.json()

# Download audio
for analysis in analyses["gameAnalyses"]:
    audio_url = f"{BASE_URL}{analysis['audioUrl']}"
    audio_response = requests.get(audio_url)
    with open(f"{analysis['gameId']}.mp3", "wb") as f:
        f.write(audio_response.content)
```

## Project Structure

```
backend/
├── main_fastapi.py              # FastAPI REST API server
├── find_champion_games.py       # Game fetching with sparse JSON
├── split_timeline.py            # Phase splitting (early/mid/late)
├── timeline_handler.py          # Timeline processing utilities
├── prompt.py                    # Phase-based AI prompts
├── make_analysis.py             # Phase-based Claude AI analysis
├── make_json_efficient.py       # Sparse JSON optimization
├── create_audio.py              # ElevenLabs audio generation
├── pyproject.toml               # Project dependencies (uv)
├── uv.lock                      # Locked dependencies
├── requirements.txt             # Dependencies (pip fallback)
├── Dockerfile                   # Docker configuration
├── .dockerignore                # Docker ignore rules
├── README.md                    # This file
│
└── {champion_name}/             # Auto-created per champion
    ├── game_YYYYMMDD_XXXX_log.json              # Match data (~150KB)
    ├── game_YYYYMMDD_XXXX_timeline.json         # Full timeline (sparse, ~1.2MB)
    ├── game_YYYYMMDD_XXXX_analysis.mp3          # Audio review
    └── {champion}_global_analysis.mp3          # Global analysis (if multiple games)
```

## Analysis Architecture

### Single-Pass Analysis (Default)

The current implementation uses **single-pass analysis** as the default:

- **Process**: Analyzes entire match log + timeline in one comprehensive Claude API call
- **Context Window**: Uses Claude's beta API with extended 1M token context
- **Data Optimization**: 
  - Match Log: ~3,700 lines (~150KB)
  - Timeline (original): ~47,000 lines (~2MB) → **306K tokens!**
  - Timeline (sparse): ~35,000 lines (~1.2MB) → **50% reduction**
- **Benefits**:
  - ✅ Single API call (faster, cheaper)
  - ✅ Complete game context in one analysis
  - ✅ No synthesis step needed
  - ✅ ~50% token reduction through sparse JSON
  - ✅ Uses Claude's extended context capabilities

**Cost**: ~$1 per game (single API call with long context)

### Phase-Based Analysis (Optional)

Phase-based analysis is still available as an alternative:

1. **Stage 1**: Analyze match log → Generate context summary
2. **Stage 2**: Analyze early game (0-15 min) → ~81K tokens
3. **Stage 3**: Analyze mid game (15-30 min) → ~117K tokens
4. **Stage 4**: Analyze late game (30+ min) → ~103K tokens
5. **Stage 5**: Synthesize all phases → Final coaching review

**Benefits:**
- ✅ Phase-specific coaching (laning tips, teamfight analysis, late-game decisions)
- ✅ More granular analysis per phase
- ✅ Better for very long games

**Cost**: ~$2 per game (5 API calls)

To use phase-based analysis, pass `use_single_pass=False` to `analyze_match_async()`.
