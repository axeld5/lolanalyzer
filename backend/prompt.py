"""
Two-stage analysis prompts for League of Legends match review.

Stage 1: Match Log Analysis - Extract game context and player performance
Stage 2: Timeline Analysis - Detailed moment-by-moment gameplay with context
"""
import json
from typing import Any, Dict, List, Union


def round_numbers_in_data(data: Any, decimals: int = 3) -> Any:
    """
    Recursively round all numbers in a data structure to specified decimal places.
    This significantly reduces token usage when sending JSON to Claude.
    
    Args:
        data: Dict, list, or any JSON-serializable data
        decimals: Number of decimal places (default: 3)
    
    Returns:
        Data with all floats rounded to specified decimals
    """
    if isinstance(data, dict):
        return {key: round_numbers_in_data(value, decimals) for key, value in data.items()}
    elif isinstance(data, list):
        return [round_numbers_in_data(item, decimals) for item in data]
    elif isinstance(data, float):
        return round(data, decimals)
    else:
        return data

# ============================================================================
# STAGE 1: MATCH LOG ANALYSIS
# ============================================================================

MATCH_LOG_ANALYSIS_PROMPT = """You are an expert League of Legends analyst. You will analyze the MATCH LOG data to understand the overall game and player performance.

Your goal is to extract key information and provide a high-level analysis that will be used to inform a detailed timeline review.

You will receive the MATCH LOG containing:
- Final game statistics
- All player performance data
- Team compositions
- Final builds and runes
- End-game metrics (damage, gold, CS, KDA, etc.)

Focus on the TARGET PLAYER and provide:

## 1. GAME CONTEXT SUMMARY
- Champion, role, and lane matchup
- Game result (W/L) and duration
- Team compositions (both teams)
- Final score and gold difference
- Game type and queue (ranked/normal/ARAM)

## 2. PLAYER PERFORMANCE METRICS
- Final KDA and kill participation %
- CS/min and total gold earned
- Damage dealt (total, to champions, taken)
- Vision score and control wards
- Objectives taken/participated in
- Performance grade (S/A/B/C/D/F) with reasoning

## 3. BUILD AND RUNES ANALYSIS
- Rune choices - appropriate for matchup?
- Item build path and final build
- Build effectiveness for the game state
- Any notable build decisions (good or questionable)

## 4. COMPARATIVE ANALYSIS
- How did they compare to their lane opponent?
- How did they compare to their role on enemy team?
- Standout stats (top damage, CS lead, etc.)
- Any glaring weaknesses in stats?

## 5. DEATH ANALYSIS
- Total deaths and when they occurred (timestamps if available)
- Were deaths in good fights or solo misplays?
- Death timers - any critical late game deaths?

## 6. TEAM CONTRIBUTION
- Damage share % vs team
- Gold share % vs team
- Objective participation
- How much did they enable team vs solo carry?

## 7. KEY CONTEXT FOR TIMELINE REVIEW
Summarize the most important things to look for in the detailed timeline:
- Key moments or turning points to investigate
- Specific time periods that need deep analysis
- Questions to answer in timeline review (e.g., "Why did they die 3 times before 10 minutes?")

FORMAT YOUR RESPONSE AS A STRUCTURED SUMMARY - NOT a spoken review yet. Use clear sections and bullet points. This will be fed into the timeline analysis.

Be analytical and factual. Save the coaching tone for the final output."""


# ============================================================================
# STAGE 2: PHASE-SPECIFIC TIMELINE ANALYSIS
# ============================================================================

EARLY_GAME_PROMPT = """You are an expert League of Legends coach analyzing the EARLY GAME phase (0-15 minutes).

You will receive:
1. MATCH CONTEXT - Overall game summary and player performance
2. EARLY GAME TIMELINE (0-15 min) - Frame-by-frame data for the laning phase

Focus on laning phase performance with specific timestamps:

## EARLY GAME ANALYSIS (0-15 minutes)
- Lane matchup and initial strategy
- CS patterns and item timings (first back, first item)
- First blood / early kills and deaths - what happened?
- Trading patterns and wave management
- Jungle interactions (ganks received/survived, invades)
- Vision control and ward placements
- Level advantages/disadvantages and why
- Early rotations or roams
- Tower plates taken/lost

GUIDELINES:
- Reference specific timestamps (e.g., "at 8:30")
- Be detailed about the laning phase
- Identify good habits and mistakes
- Keep it conversational and direct
- This will be combined with mid and late game analysis

Provide your early game analysis:"""


MID_GAME_PROMPT = """You are an expert League of Legends coach analyzing the MID GAME phase (15-30 minutes).

You will receive:
1. MATCH CONTEXT - Overall game summary and player performance
2. EARLY GAME SUMMARY - What happened in laning phase
3. MID GAME TIMELINE (15-30 min) - Frame-by-frame data for mid game

Focus on teamfighting and objective play with specific timestamps:

## MID GAME ANALYSIS (15-30 minutes)
- Transition from laning to mid game
- Major teamfights - positioning, target selection, execution
- Objective contests (dragons, herald, towers, baron setup)
- Map movements and rotations
- Item power spikes and their utilization
- Deaths and their impact on objectives
- Vision control and map awareness
- Team coordination and shot-calling influence
- Critical mistakes or excellent plays with timestamps

GUIDELINES:
- Reference specific timestamps for teamfights and objectives
- Analyze decision-making in fights
- Identify macro play patterns
- Keep it conversational and direct
- This will be combined with early and late game analysis

Provide your mid game analysis:"""


LATE_GAME_PROMPT = """You are an expert League of Legends coach analyzing the LATE GAME phase (30+ minutes).

You will receive:
1. MATCH CONTEXT - Overall game summary and player performance
2. EARLY GAME SUMMARY - What happened in laning phase
3. MID GAME SUMMARY - What happened in mid game
4. LATE GAME TIMELINE (30+ min) - Frame-by-frame data for late game

Focus on high-stakes moments and game-ending plays with specific timestamps:

## LATE GAME ANALYSIS (30+ minutes)
- Final teamfights and their outcomes
- Baron/Elder dragon fights - positioning and execution
- Death timers and their impact
- Game-ending plays or mistakes
- Risk management and decision-making
- Itemization for late game
- Positioning in team fights
- How the game was won or lost

GUIDELINES:
- Reference specific timestamps for crucial moments
- Emphasize decision-making under pressure
- Identify what sealed the victory or caused the loss
- Keep it conversational and direct
- This completes the phase-by-phase analysis

Provide your late game analysis:"""


FINAL_SYNTHESIS_PROMPT = """You are an expert League of Legends coach synthesizing a complete VOD review.

You will receive:
1. MATCH CONTEXT - Overall game statistics and performance
2. EARLY GAME ANALYSIS - Detailed laning phase review (0-15 min)
3. MID GAME ANALYSIS - Detailed mid game review (15-30 min)
4. LATE GAME ANALYSIS - Detailed late game review (30+ min)

Your goal is to synthesize these analyses into a cohesive, engaging spoken review.

Create a natural, flowing coaching review with these sections:

## 1. INTRODUCTION (30 seconds)
- Welcome and game overview (champion, result, overall grade)
- Set the tone for the review

## 2. EARLY GAME (1.5 minutes)
- Synthesize the early game analysis into a flowing narrative
- Keep the specific timestamps and key moments
- Make it engaging and conversational

## 3. MID GAME (1.5 minutes)
- Synthesize the mid game analysis into a flowing narrative
- Connect to early game momentum
- Highlight turning points

## 4. LATE GAME (1 minute)
- Synthesize the late game analysis into a flowing narrative
- Explain how the game was won/lost
- Key final moments

## 5. KEY STRENGTHS (30 seconds)
- 2-3 specific excellent plays across all phases
- Positive reinforcement

## 6. AREAS FOR IMPROVEMENT (45 seconds)
- 3-4 specific mistakes or patterns across all phases
- Constructive criticism with examples

## 7. ACTIONABLE RECOMMENDATIONS (45 seconds)
- 3-5 concrete practice points
- Prioritized by impact
- Reference specific examples from the game

IMPORTANT GUIDELINES:
- Write for SPOKEN delivery - natural, conversational, engaging
- Use "you" and "your" - speak directly to the player
- Flow naturally between sections - don't announce section numbers
- Be constructive and balanced - coaching, not criticism
- Total length: ~5-6 minutes when spoken
- Make it motivating and actionable
- Sound like you're watching the VOD together

START YOUR COACHING REVIEW NOW:"""


# ============================================================================
# PROMPT GENERATORS
# ============================================================================

def get_match_log_prompt(match_log: dict, player_puuid: str) -> str:
    """
    Generate Stage 1 prompt for match log analysis.
    
    Args:
        match_log: The match log JSON data
        player_puuid: The PUUID of the player to analyze
    
    Returns:
        Complete prompt string for match log analysis
    """
    # Find the target player's data
    participants = match_log.get("info", {}).get("participants", [])
    target_player = None
    for participant in participants:
        if participant.get("puuid") == player_puuid:
            target_player = participant
            break
    
    if not target_player:
        raise ValueError("Player not found in match data")
    
    # Extract key info for context
    champion_name = target_player.get("championName", "Unknown")
    game_name = target_player.get("riotIdGameName", "Unknown")
    tag_line = target_player.get("riotIdTagline", "")
    
    # Round all numbers to 3 decimals to reduce token usage
    print("  → Rounding numbers to 3 decimals to optimize token usage...")
    match_log_rounded = round_numbers_in_data(match_log, decimals=3)
    match_log_str = json.dumps(match_log_rounded, indent=2)
    
    prompt = f"""{MATCH_LOG_ANALYSIS_PROMPT}

TARGET PLAYER INFORMATION:
- Summoner: {game_name}#{tag_line}
- Champion: {champion_name}
- PUUID: {player_puuid}

MATCH LOG DATA:
```json
{match_log_str}
```

Provide your structured analysis now:"""
    
    return prompt


def get_phase_prompt(phase_name: str, phase_timeline: dict, match_context: str,
                     previous_analyses: dict, player_puuid: str, champion_name: str) -> str:
    """
    Generate prompt for a specific game phase analysis.
    
    Args:
        phase_name: Name of the phase ("early", "mid", or "late")
        phase_timeline: The timeline JSON data for this phase
        match_context: The summary from Stage 1 analysis
        previous_analyses: Dict of previous phase analyses {"early": "...", "mid": "..."}
        player_puuid: The PUUID of the player to analyze
        champion_name: The champion name
    
    Returns:
        Complete prompt string for phase analysis
    """
    # Select the appropriate prompt
    phase_prompts = {
        "early": EARLY_GAME_PROMPT,
        "mid": MID_GAME_PROMPT,
        "late": LATE_GAME_PROMPT
    }
    
    base_prompt = phase_prompts.get(phase_name, EARLY_GAME_PROMPT)
    
    # Round all numbers to 3 decimals to reduce token usage
    print(f"  → Rounding numbers to 3 decimals to optimize token usage...")
    timeline_rounded = round_numbers_in_data(phase_timeline, decimals=3)
    timeline_str = json.dumps(timeline_rounded, indent=2)
    
    prompt = f"""{base_prompt}

TARGET PLAYER:
- Champion: {champion_name}
- PUUID: {player_puuid}

MATCH CONTEXT (from statistical analysis):
{match_context}
"""
    
    # Add previous phase analyses if available
    if "early" in previous_analyses and phase_name in ["mid", "late"]:
        prompt += f"""
EARLY GAME SUMMARY:
{previous_analyses["early"]}
"""
    
    if "mid" in previous_analyses and phase_name == "late":
        prompt += f"""
MID GAME SUMMARY:
{previous_analyses["mid"]}
"""
    
    prompt += f"""
{phase_name.upper()} GAME TIMELINE DATA:
```json
{timeline_str}
```

Begin your {phase_name} game analysis:"""
    
    return prompt


def get_synthesis_prompt(match_context: str, phase_analyses: dict, champion_name: str) -> str:
    """
    Generate prompt for final synthesis of all phase analyses.
    
    Args:
        match_context: The summary from Stage 1 analysis
        phase_analyses: Dict of phase analyses {"early": "...", "mid": "...", "late": "..."}
        champion_name: The champion name
    
    Returns:
        Complete prompt string for final synthesis
    """
    prompt = f"""{FINAL_SYNTHESIS_PROMPT}

TARGET CHAMPION: {champion_name}

MATCH CONTEXT (from statistical analysis):
{match_context}

EARLY GAME ANALYSIS (0-15 minutes):
{phase_analyses.get("early", "No early game data")}

MID GAME ANALYSIS (15-30 minutes):
{phase_analyses.get("mid", "No mid game data")}

LATE GAME ANALYSIS (30+ minutes):
{phase_analyses.get("late", "No late game data")}

Now synthesize this into a cohesive, engaging coaching review:"""
    
    return prompt


def get_timeline_prompt(timeline: dict, match_context: str, player_puuid: str, champion_name: str) -> str:
    """
    DEPRECATED: Use phase-based analysis instead (get_phase_prompt + get_synthesis_prompt).
    This function is kept for backwards compatibility but the full timeline is very token-heavy.
    
    Args:
        timeline: The timeline JSON data
        match_context: The summary from Stage 1 analysis
        player_puuid: The PUUID of the player to analyze
        champion_name: The champion name
    
    Returns:
        Complete prompt string for timeline analysis
    """
    raise NotImplementedError(
        "Full timeline analysis is deprecated due to token limits. "
        "Use phase-based analysis: get_phase_prompt() for each phase, then get_synthesis_prompt()"
    )


def get_analysis_prompt(match_log: dict, timeline: dict, player_puuid: str) -> str:
    """
    DEPRECATED: Use two-stage analysis instead (get_match_log_prompt + get_timeline_prompt).
    This function is kept for backwards compatibility but will be very token-heavy.
    
    Args:
        match_log: The match log JSON data
        timeline: The timeline JSON data
        player_puuid: The PUUID of the player to analyze
    
    Returns:
        Complete prompt string with embedded JSON data
    """
    raise NotImplementedError(
        "Single-stage analysis is deprecated due to token limits. "
        "Use two-stage analysis: get_match_log_prompt() then get_timeline_prompt()"
    )


def get_summary_prompt() -> str:
    """
    Returns a shorter prompt for quick summaries (under 1 minute).
    """
    return """Provide a concise 30-45 second summary of this game covering:
- Champion and role
- Final KDA and result
- One key strength
- One key improvement area
- Overall grade

Keep it conversational and direct."""

