"""
FastAPI wrapper for League of Legends match analysis pipeline.

Provides REST API endpoints for:
1. Fetching champion games for a player
2. Analyzing selected games
3. Downloading audio files
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from find_champion_games import get_puuid_from_riot_id, find_champion_games
from make_analysis import analyze_match_async, synthesize_global_analysis
from create_audio import text_to_speech, get_voice_id, VOICES
from timeline_handler import ensure_timeline_processed

load_dotenv()

app = FastAPI(title="LoL Analyzer API", version="1.0.0")

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class FetchGamesRequest(BaseModel):
    game_name: str
    tag: str
    champion: str


class GameInfo(BaseModel):
    id: str  # base_filename
    match_id: str
    champion: str
    result: str  # "Victory" or "Defeat"
    kda: str  # "K/D/A"
    duration: str  # "MM:SS"
    date: str  # "YYYY-MM-DD"


class FetchGamesResponse(BaseModel):
    games: List[GameInfo]
    champion: str
    puuid: str


class AnalyzeGamesRequest(BaseModel):
    game_ids: List[str]  # List of base_filenames
    champion: str
    puuid: str
    voice: Optional[str] = "george"


class PhaseAnalysis(BaseModel):
    early: Optional[str] = None
    mid: Optional[str] = None
    late: Optional[str] = None


class GameAnalysis(BaseModel):
    gameId: str  # base_filename
    match_id: str
    champion: str
    audioUrl: str  # URL to download audio
    summary: str  # Final review summary
    detailedAnalysis: Optional[str] = None  # Full final review
    phaseAnalyses: Optional[PhaseAnalysis] = None


class AnalyzeGamesResponse(BaseModel):
    gameAnalyses: List[GameAnalysis]
    globalAnalysisUrl: Optional[str] = None
    globalSummary: Optional[str] = None
    globalDetailedAnalysis: Optional[str] = None


def format_duration(seconds: int) -> str:
    """Convert seconds to MM:SS format."""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


def format_date(timestamp_ms: int) -> str:
    """Convert timestamp to YYYY-MM-DD format."""
    from datetime import datetime
    return datetime.fromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d")


@app.post("/api/fetch-games", response_model=FetchGamesResponse)
async def fetch_games(request: FetchGamesRequest):
    """
    Fetch latest champion games for a player.
    
    Args:
        request: Contains game_name, tag, and champion
        
    Returns:
        List of games with basic info (id, champion, result, kda, duration, date)
    """
    try:
        # Get PUUID from Riot ID
        puuid = get_puuid_from_riot_id(request.game_name, request.tag)
        if not puuid:
            raise HTTPException(
                status_code=404,
                detail=f"Could not find player with Riot ID {request.game_name}#{request.tag}"
            )
        
        # Find champion games
        champion_games = find_champion_games(
            puuid, 
            request.champion, 
            save_to_folder=True
        )
        
        if not champion_games:
            raise HTTPException(
                status_code=404,
                detail=f"No {request.champion} games found in latest 20 matches"
            )
        
        # Format games for frontend
        games = []
        for game in champion_games:
            player_stats = game["player_stats"]
            match_info = game["match_data"]["info"]
            
            # Get base_filename (either from game_info or generate from match_id)
            base_filename = game.get("base_filename")
            if not base_filename:
                # Fallback: use match_id as base (though this shouldn't happen if save_to_folder=True)
                base_filename = game["match_id"]
            
            # Format result
            result = "Victory" if player_stats.get("win") else "Defeat"
            
            # Format KDA
            kda = f"{player_stats.get('kills', 0)}/{player_stats.get('deaths', 0)}/{player_stats.get('assists', 0)}"
            
            # Format duration
            duration_seconds = match_info.get("gameDuration", 0)
            duration = format_duration(duration_seconds)
            
            # Format date
            game_creation = match_info.get("gameCreation", 0)
            date = format_date(game_creation)
            
            games.append(GameInfo(
                id=base_filename,
                match_id=game["match_id"],
                champion=player_stats.get("championName", request.champion),
                result=result,
                kda=kda,
                duration=duration,
                date=date
            ))
        
        return FetchGamesResponse(
            games=games,
            champion=request.champion,
            puuid=puuid
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching games: {str(e)}")


@app.post("/api/analyze-games", response_model=AnalyzeGamesResponse)
async def analyze_games(request: AnalyzeGamesRequest):
    """
    Analyze selected games and generate audio reviews.
    
    Args:
        request: Contains game_ids (base_filenames), champion, puuid, and optional voice
        
    Returns:
        List of game analyses with audio URLs and optional global analysis
    """
    try:
        # Validate voice
        if request.voice not in VOICES:
            request.voice = "george"
        
        # Get champion folder
        champion_folder_name = request.champion.lower().replace(" ", "_").replace("'", "")
        champion_folder = Path(champion_folder_name)
        
        if not champion_folder.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Champion folder '{champion_folder_name}' not found. Please fetch games first."
            )
        
        # Load match data for selected games
        matches_to_analyze = []
        for game_id in request.game_ids:
            log_file = champion_folder / f"{game_id}_log.json"
            timeline_file = champion_folder / f"{game_id}_timeline.json"
            
            if not log_file.exists() or not timeline_file.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Game files not found for {game_id}"
                )
            
            # Load match data
            with open(log_file, 'r') as f:
                match_log = json.load(f)
            with open(timeline_file, 'r') as f:
                timeline = json.load(f)
            
            # Ensure timeline is processed (has formattedTimestamp and isOnSide)
            timeline = ensure_timeline_processed(timeline, str(timeline_file))
            
            match_id = match_log.get("metadata", {}).get("matchId", game_id)
            
            matches_to_analyze.append({
                'base_filename': game_id,
                'match_id': match_id,
                'match_log': match_log,
                'timeline': timeline
            })
        
        # Analyze all matches in parallel
        print(f"\n🚀 Analyzing {len(matches_to_analyze)} games in parallel...")
        
        async def analyze_all_matches():
            tasks = []
            for match_info in matches_to_analyze:
                task = analyze_match_async(
                    match_info['match_log'],
                    match_info['timeline'],
                    request.puuid,
                    match_id=match_info['match_id']
                )
                tasks.append((match_info['base_filename'], match_info['match_id'], task))
            
            results = await asyncio.gather(*[task for _, _, task in tasks])
            
            return {
                base_filename: (match_id, result)
                for (base_filename, match_id, _), result in zip(tasks, results)
            }
        
        all_results = await analyze_all_matches()
        
        # Create a mapping of base_filename to match_log for champion name extraction
        match_log_map = {m['base_filename']: m['match_log'] for m in matches_to_analyze}
        
        # Generate audio files and format responses
        game_analyses = []
        voice_id = get_voice_id(request.voice)
        
        for base_filename, (match_id, (match_context, phase_analyses, final_review)) in all_results.items():
            # Generate audio file
            audio_filename = f"{base_filename}_analysis.mp3"
            audio_path = champion_folder / audio_filename
            
            try:
                text_to_speech(final_review, str(audio_path), voice_id=voice_id)
                audio_url = f"/api/audio/{champion_folder_name}/{audio_filename}"
            except Exception as e:
                print(f"⚠️  Error generating audio for {base_filename}: {e}")
                audio_url = None
            
            # Extract champion name from match log
            champion_name = request.champion
            match_log = match_log_map.get(base_filename)
            if match_log:
                participants = match_log.get("info", {}).get("participants", [])
                for participant in participants:
                    if participant.get("puuid") == request.puuid:
                        champion_name = participant.get("championName", request.champion)
                        break
            
            # Create summary from final review (first sentence or 200 chars)
            # Try to get first meaningful sentence
            summary = final_review.strip()
            # Find first sentence ending
            for delimiter in ['. ', '!\n', '?\n', '.\n']:
                if delimiter in summary:
                    summary = summary.split(delimiter)[0] + '.'
                    break
            # Limit length
            if len(summary) > 200:
                summary = summary[:197] + "..."
            
            # Format phase analyses
            phase_analysis_obj = None
            if phase_analyses:
                phase_analysis_obj = PhaseAnalysis(
                    early=phase_analyses.get("early"),
                    mid=phase_analyses.get("mid"),
                    late=phase_analyses.get("late")
                )
            
            game_analyses.append(GameAnalysis(
                gameId=base_filename,
                match_id=match_id,
                champion=champion_name,
                audioUrl=audio_url or "",
                summary=summary,
                detailedAnalysis=final_review,
                phaseAnalyses=phase_analysis_obj
            ))
        
        # Generate global analysis if multiple games
        global_analysis_url = None
        global_summary = None
        
        if len(all_results) >= 2:
            try:
                # Convert results format for global analysis
                global_results = {
                    match_id: result 
                    for _, (match_id, result) in all_results.items()
                }
                global_analysis = synthesize_global_analysis(global_results)
                
                # Generate audio for global analysis
                global_audio_filename = f"{request.champion}_global_analysis.mp3"
                global_audio_path = champion_folder / global_audio_filename
                
                try:
                    text_to_speech(global_analysis, str(global_audio_path), voice_id=voice_id)
                    global_analysis_url = f"/api/audio/{champion_folder_name}/{global_audio_filename}"
                except Exception as e:
                    print(f"⚠️  Error generating global audio: {e}")
                
                # Create summary (first sentence or 300 chars)
                global_summary = global_analysis.strip()
                for delimiter in ['. ', '!\n', '?\n', '.\n']:
                    if delimiter in global_summary:
                        global_summary = global_summary.split(delimiter)[0] + '.'
                        break
                if len(global_summary) > 300:
                    global_summary = global_summary[:297] + "..."
                
                # Store full analysis for detailed view
                global_detailed_analysis = global_analysis.strip()
                    
            except Exception as e:
                print(f"⚠️  Error during global analysis: {e}")
                global_detailed_analysis = None
        
        return AnalyzeGamesResponse(
            gameAnalyses=game_analyses,
            globalAnalysisUrl=global_analysis_url,
            globalSummary=global_summary,
            globalDetailedAnalysis=global_detailed_analysis if 'global_detailed_analysis' in locals() else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing games: {str(e)}")


@app.get("/api/audio/{champion}/{filename}")
async def download_audio(champion: str, filename: str):
    """
    Download audio file for a game analysis.
    
    Args:
        champion: Champion folder name
        filename: Audio filename (e.g., game_20251112_XXXX_analysis.mp3)
        
    Returns:
        Audio file (MP3)
    """
    try:
        champion_folder = Path(champion.lower().replace(" ", "_").replace("'", ""))
        audio_path = champion_folder / filename
        
        if not audio_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Audio file not found: {filename}"
            )
        
        # Validate that it's an audio file
        if not filename.endswith('.mp3'):
            raise HTTPException(
                status_code=400,
                detail="Only MP3 files are supported"
            )
        
        return FileResponse(
            path=str(audio_path),
            media_type="audio/mpeg",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading audio: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "LoL Analyzer API is running"}


@app.get("/api/voices")
async def get_voices():
    """Get available voices."""
    return {"voices": list(VOICES.keys())}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

