# LoL Analyzer

An advanced AI-powered web application for analyzing League of Legends gameplay replays. Get detailed insights, audio summaries, and personalized feedback to elevate your gameplay.

## 🎮 Overview

LoL Analyzer is a full-stack application that combines:
- **Backend**: FastAPI server that fetches match data from Riot Games API and performs AI-powered analysis using Claude
- **Frontend**: Modern React web application with a beautiful UI for interacting with the analysis system

The system analyzes your League of Legends matches, provides comprehensive coaching insights, and generates audio summaries you can listen to while playing or commuting.

## ✨ Features

### Core Capabilities
- **Champion Game Discovery**: Find all games where you played a specific champion from your latest 20 matches
- **AI-Powered Match Analysis**: Comprehensive analysis using Claude 4.5 Sonnet with extended context (1M tokens)
  - Single-pass analysis: Processes entire match in one comprehensive review
  - Phase-based analysis: Granular early/mid/late game breakdowns (optional)
- **Audio Review Generation**: Convert text analysis to natural-sounding audio using ElevenLabs TTS
- **Advanced Data Optimization**: 
  - Sparse JSON and delta encoding reduce token usage by 40-60%
  - Team side detection (Blue/Red)
  - Optimized data reduces AI analysis costs significantly

### User Experience
- **Modern Web Interface**: Beautiful, responsive UI built with React, TypeScript, and shadcn/ui
- **Game Selection**: Browse and select specific games to analyze
- **Downloadable Results**: Download audio analysis files for offline listening
- **Global Analysis**: Get insights across multiple games for pattern recognition

## 🏗️ Architecture

```
lolanalyzer/
├── backend/          # FastAPI Python backend
│   ├── FastAPI REST API server
│   ├── Riot Games API integration
│   ├── Claude AI analysis engine
│   └── ElevenLabs audio generation
│
└── replay-sage/      # React TypeScript frontend
    ├── React 18 + TypeScript
    ├── shadcn/ui components
    └── Tailwind CSS styling
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (for backend)
- **Node.js v18+** (for frontend)
- **API Keys**:
  - Riot Games API key ([Get one here](https://developer.riotgames.com/))
  - Anthropic API key ([Get one here](https://console.anthropic.com/))
  - ElevenLabs API key ([Get one here](https://elevenlabs.io/))

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies using `uv`:
```bash
# Create virtual environment and install dependencies
uv venv
uv sync

# Activate the virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows
```

3. Create a `.env` file in the `backend` directory:
```env
# Riot Games API
RIOT_API_KEY=your_riot_api_key_here
PUUID=your_puuid_here  # Optional, can use Riot ID instead

# Claude AI (for match analysis)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# ElevenLabs (for audio generation)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

4. Start the FastAPI server:
```bash
# Using uvicorn directly
uvicorn main_fastapi:app --host 0.0.0.0 --port 8000 --reload

# Or using uv
uv run uvicorn main_fastapi:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd replay-sage
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the `replay-sage` directory:
```env
VITE_API_URL=http://localhost:8000
```

4. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173` (or the port Vite assigns).

## 🐳 Docker Setup (Backend)

You can also run the backend using Docker:

```bash
cd backend

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
docker run -d \
  --name lolanalyzer-backend \
  -p 8000:8000 \
  --env-file .env \
  lolanalyzer-backend
```

## 📖 Usage

### Web Application Workflow

1. **Enter Your Information**: 
   - Input your Riot ID in the format `GameName#Tag` (e.g., `Player#NA1`)
   - Enter the champion you want to analyze

2. **Select Games**: 
   - Browse through your recent matches for that champion
   - Select the games you want to analyze

3. **View Analysis**: 
   - Wait for the AI to analyze your selected games
   - Review individual game analyses and the global summary
   - Expand cards to see detailed breakdowns
   - Download audio summaries for offline listening

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
      "phaseAnalyses": null
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

#### 4. Health Check
`GET /api/health`

Check if the API is running.

#### 5. Get Available Voices
`GET /api/voices`

Get list of available ElevenLabs voices.

### Standalone Scripts (CLI)

The backend also provides standalone scripts for direct use:

#### Fetch Games Only
```bash
cd backend
python find_champion_games.py
```

#### Analyze a Match
```bash
python make_analysis.py <log_file> <timeline_file> <player_puuid>
```

#### Convert Analysis to Audio
```bash
python create_audio.py <text_file> <output_file> <voice>
```

## 🎙️ Available Voices

Choose from these ElevenLabs voices (use with `voice` parameter in API requests):
- **george** (default) - Clear, professional
- **adam** - Deep, authoritative
- **bill** - Warm, friendly
- **callum** - Young, energetic
- **charlie** - British, natural

Get the full list via `GET /api/voices`

## 💰 Cost Estimates

- **Single-Pass Analysis**: ~$1 per game (single API call with extended context)
- **Phase-Based Analysis**: ~$2 per game (5 API calls for granular analysis)
- **Data Optimization**: Reduces costs by 40-60% through sparse JSON and delta encoding

## 📁 Project Structure

```
lolanalyzer/
├── backend/
│   ├── main_fastapi.py              # FastAPI REST API server
│   ├── find_champion_games.py       # Game fetching with sparse JSON
│   ├── split_timeline.py            # Phase splitting (early/mid/late)
│   ├── timeline_handler.py          # Timeline processing utilities
│   ├── prompt.py                    # Phase-based AI prompts
│   ├── make_analysis.py             # Claude AI analysis
│   ├── make_json_efficient.py       # Sparse JSON optimization
│   ├── create_audio.py              # ElevenLabs audio generation
│   ├── pyproject.toml               # Project dependencies (uv)
│   ├── Dockerfile                   # Docker configuration
│   └── README.md                    # Detailed backend documentation
│
└── replay-sage/
    ├── src/
    │   ├── components/              # React components
    │   │   ├── ui/                  # shadcn/ui components
    │   │   ├── SummonerForm.tsx     # Form for entering Riot ID
    │   │   ├── GameList.tsx         # List of games to select
    │   │   └── AnalysisResults.tsx  # Display analysis results
    │   ├── pages/                   # Page components
    │   │   ├── Index.tsx            # Main page with workflow
    │   │   └── NotFound.tsx         # 404 page
    │   ├── lib/                     # Utility functions
    │   │   ├── api.ts               # API client functions
    │   │   └── utils.ts             # General utilities
    │   └── App.tsx                  # Root component
    ├── package.json
    └── README.md                    # Detailed frontend documentation
```

## 🔧 Tech Stack

### Backend
- **Framework**: FastAPI
- **Python**: 3.8+
- **Package Manager**: uv
- **AI**: Claude 4.5 Sonnet (Anthropic)
- **TTS**: ElevenLabs
- **API**: Riot Games API

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Styling**: Tailwind CSS
- **State Management**: React Query (TanStack Query)
- **Routing**: React Router DOM
- **Form Handling**: React Hook Form with Zod validation
- **Markdown Rendering**: react-markdown

## 📚 Analysis Architecture

### Single-Pass Analysis (Default)

The current implementation uses **single-pass analysis** as the default:

- **Process**: Analyzes entire match log + timeline in one comprehensive Claude API call
- **Context Window**: Uses Claude's beta API with extended 1M token context
- **Data Optimization**: 
  - Match Log: ~3,700 lines (~150KB)
  - Timeline (sparse): ~35,000 lines (~1.2MB) → **50% reduction**
- **Benefits**:
  - ✅ Single API call (faster, cheaper)
  - ✅ Complete game context in one analysis
  - ✅ No synthesis step needed
  - ✅ ~50% token reduction through sparse JSON

### Phase-Based Analysis (Optional)

Phase-based analysis is available as an alternative:

1. **Stage 1**: Analyze match log → Generate context summary
2. **Stage 2**: Analyze early game (0-15 min)
3. **Stage 3**: Analyze mid game (15-30 min)
4. **Stage 4**: Analyze late game (30+ min)
5. **Stage 5**: Synthesize all phases → Final coaching review

**Benefits:**
- ✅ Phase-specific coaching (laning tips, teamfight analysis, late-game decisions)
- ✅ More granular analysis per phase
- ✅ Better for very long games

## 🧪 Development

### Backend Development

```bash
cd backend
source .venv/bin/activate
uvicorn main_fastapi:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Development

```bash
cd replay-sage
npm run dev
```

### Available Scripts (Frontend)

- `npm run dev` - Start the development server with hot reload
- `npm run build` - Build the application for production
- `npm run build:dev` - Build the application in development mode
- `npm run preview` - Preview the production build locally
- `npm run lint` - Run ESLint to check for code issues

## 📝 Environment Variables

### Backend (.env in `backend/` directory)
```env
RIOT_API_KEY=your_riot_api_key_here
PUUID=your_puuid_here  # Optional
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

### Frontend (.env in `replay-sage/` directory)
```env
VITE_API_URL=http://localhost:8000
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is private and proprietary.

## 📖 Additional Documentation

For more detailed information, see:
- [Backend README](backend/README.md) - Detailed backend documentation, API reference, and examples
- [Frontend README](replay-sage/README.md) - Detailed frontend documentation and component structure

## 🆘 Support

For issues or questions, please open an issue in the repository.

