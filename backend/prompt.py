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
- **Side played (Red/Blue)** - important for objectives and camera angle
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
   - Each participantFrame includes championName field
   - Each event includes championName for the participant
   - Kill events include killerChampionName and victimChampionName

**IMPORTANT**: Focus ONLY on the early game phase. Do not discuss mid or late game events. Your analysis will be combined with separate mid and late game analyses later.

## EARLY GAME ANALYSIS (0-15 minutes)
Analyze the laning phase with specific timestamps:
- Lane matchup and initial strategy
- CS patterns and item timings (first back, first item)
- First blood / early kills and deaths - what happened?
- Trading patterns and wave management
- Jungle interactions (ganks received/survived, invades)
- Vision control and ward placements
- Level advantages/disadvantages and why
- Early rotations or roams
- Tower plates taken/lost

## HIDDEN MECHANICS & MICRO PLAY ANALYSIS
Look for champion-specific execution details that stats don't show:
- Skill shot accuracy and positioning
- Ability combo execution (e.g., Lillia E-W sweet spot consistency)
- Resource management (mana, energy, cooldowns)
- Auto-attack weaving and trading stance
- Ability usage efficiency (wasted abilities, missed opportunities)
- Positioning micro-mistakes that led to taking extra damage
- Champion-specific mechanics (e.g., spacing for abilities, passive stacks)

GUIDELINES:
- Reference specific timestamps (e.g., "at 8:30")
- Champion names are directly in the data (championName field)
- Be detailed and analytical about the laning phase
- Look beyond stats to identify execution issues
- Identify good habits and mistakes with examples
- Keep it conversational and direct
- Stay focused on 0-15 minutes ONLY

Provide your early game analysis:"""


MID_GAME_PROMPT = """You are an expert League of Legends coach analyzing the MID GAME phase (15-30 minutes).

You will receive:
1. MATCH CONTEXT - Overall game summary and player performance
2. MID GAME TIMELINE (15-30 min) - Frame-by-frame data for mid game
   - Each participantFrame includes championName field
   - Each event includes championName for the participant
   - Kill events include killerChampionName and victimChampionName

**IMPORTANT**: Focus ONLY on the mid game phase (15-30 minutes). Do not discuss early or late game events. Your analysis will be combined with separate early and late game analyses later.

## MID GAME ANALYSIS (15-30 minutes)
Analyze teamfighting and objective play with specific timestamps:
- Transition from laning to mid game
- Major teamfights - positioning, target selection, execution
- Objective contests (dragons, herald, towers, baron setup)
- Map movements and rotations
- Item power spikes and their utilization
- Deaths and their impact on objectives
- Vision control and map awareness
- Team coordination and shot-calling influence
- Critical mistakes or excellent plays with timestamps

## HIDDEN MECHANICS & MICRO PLAY ANALYSIS
Look for execution details in teamfights and skirmishes:
- Ability usage in fights (correct target priority, timing)
- Positioning errors that led to deaths or lost fights
- Missed skill shots or abilities used on wrong targets
- Cooldown management in extended fights
- Failure to use summoner spells or items (stopwatch, QSS, etc.)
- Champion-specific mechanics in teamfights
- Overextension or hesitation in key moments
- Mechanical outplays or misplays

GUIDELINES:
- Reference specific timestamps for teamfights and objectives
- Champion names are directly in the data (championName field)
- Analyze decision-making AND execution in fights
- Look for patterns in mechanical mistakes
- Identify macro play patterns
- Keep it conversational and direct
- Stay focused on 15-30 minutes ONLY

Provide your mid game analysis:"""


LATE_GAME_PROMPT = """You are an expert League of Legends coach analyzing the LATE GAME phase (30+ minutes).

You will receive:
1. MATCH CONTEXT - Overall game summary and player performance
2. LATE GAME TIMELINE (30+ min) - Frame-by-frame data for late game
   - Each participantFrame includes championName field
   - Each event includes championName for the participant
   - Kill events include killerChampionName and victimChampionName

**IMPORTANT**: Focus ONLY on the late game phase (30+ minutes). Do not discuss early or mid game events. Your analysis will be combined with separate early and mid game analyses later.

## LATE GAME ANALYSIS (30+ minutes)
Analyze high-stakes moments and game-ending plays with specific timestamps:
- Final teamfights and their outcomes
- Baron/Elder dragon fights - positioning and execution
- Death timers and their impact
- Game-ending plays or mistakes
- Risk management and decision-making
- Itemization for late game
- Positioning in team fights
- How the game was won or lost

## HIDDEN MECHANICS & CRITICAL EXECUTION
Look for high-pressure execution details:
- Clutch ability usage or failure (crucial cc, peel, damage)
- Flash/summoner spell usage in game-deciding moments
- Positioning in high-stakes fights (one mistake = loss)
- Target selection in final teamfights
- Mechanical misplays under pressure
- Item actives usage (Zhonya's, GA timing, etc.)
- Failure to execute win condition
- Champion-specific execution in critical moments

GUIDELINES:
- Reference specific timestamps for crucial moments
- Champion names are directly in the data (championName field)
- Emphasize decision-making AND execution under pressure
- Identify what sealed the victory or caused the loss
- Look for mechanical failures in key moments
- Keep it conversational and direct
- Stay focused on 30+ minutes ONLY

Provide your late game analysis:"""


SINGLE_PASS_ANALYSIS_PROMPT = """You are an expert League of Legends coach providing a complete VOD review.

You will receive match log data and timeline data with formatted timestamps (minute:seconds:milliseconds) and isOnSide fields.

Create a natural, conversational coaching review covering:
- Game overview and result
- Key moments from early, mid, and late game with timestamps
- What went well and what could be improved
- Actionable recommendations

Write for SPOKEN delivery - natural, engaging, ~5-6 minutes when spoken. Use "you" and "your" to speak directly to the player. Reference specific timestamps and use isOnSide information when relevant.

Provide your coaching review:"""


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
# GLOBAL MULTI-GAME ANALYSIS
# ============================================================================

GLOBAL_ANALYSIS_PROMPT = """You are an expert League of Legends coach analyzing multiple games to identify patterns.

You will receive coaching reviews for multiple games. Analyze them and provide:

**What you're good at:** (4 bullet points)
- Identify 4 specific strengths that appear consistently across games
- Be specific and reference which games show these strengths

**What can be improved:** (4 bullet points)
- Identify 4 specific weaknesses or mistakes that recur across games
- Explain the impact and reference which games show these issues

Write for SPOKEN delivery - natural, conversational, ~1-2 minutes when spoken. Be direct and actionable.

Provide your multi-game analysis:"""


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
    
    # Determine side (teamId 100 = Blue, 200 = Red)
    team_id = target_player.get("teamId", 0)
    side = "Blue Side" if team_id == 100 else "Red Side" if team_id == 200 else "Unknown"
    
    # Round all numbers to 3 decimals to reduce token usage
    print("  → Rounding numbers to 3 decimals to optimize token usage...")
    match_log_rounded = round_numbers_in_data(match_log, decimals=3)
    match_log_str = json.dumps(match_log_rounded, indent=2)
    
    prompt = f"""{MATCH_LOG_ANALYSIS_PROMPT}

TARGET PLAYER INFORMATION:
- Summoner: {game_name}#{tag_line}
- Champion: {champion_name}
- Side: {side} (Team {team_id})
- PUUID: {player_puuid}

MATCH LOG DATA:
```json
{match_log_str}
```

Provide your structured analysis now:"""
    
    return prompt


def get_phase_prompt(phase_name: str, phase_timeline: dict, match_context: str,
                     player_puuid: str, champion_name: str) -> str:
    """
    Generate prompt for a specific game phase analysis (independent).
    
    Args:
        phase_name: Name of the phase ("early", "mid", or "late")
        phase_timeline: The timeline JSON data for this phase
        match_context: The summary from Stage 1 analysis
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


def get_single_pass_analysis_prompt(match_log: dict, timeline: dict, player_puuid: str, champion_name: str) -> str:
    """
    Generate prompt for single-pass analysis (log + timeline in one go).
    
    Args:
        match_log: The match log JSON data
        timeline: The timeline JSON data (should be processed with timeline_handler)
        player_puuid: The PUUID of the player to analyze
        champion_name: The champion name
    
    Returns:
        Complete prompt string for single-pass analysis
    """
    # Round all numbers to 3 decimals to reduce token usage
    print("  → Rounding numbers to 3 decimals to optimize token usage...")
    match_log_rounded = round_numbers_in_data(match_log, decimals=3)
    timeline_rounded = round_numbers_in_data(timeline, decimals=3)
    
    match_log_str = json.dumps(match_log_rounded, indent=2)
    timeline_str = json.dumps(timeline_rounded, indent=2)
    
    prompt = f"""{SINGLE_PASS_ANALYSIS_PROMPT}

TARGET PLAYER:
- Champion: {champion_name}
- PUUID: {player_puuid}

MATCH LOG DATA:
```json
{match_log_str}
```

TIMELINE DATA (with formatted timestamps and isOnSide):
```json
{timeline_str}
```

Begin your comprehensive coaching review:"""
    
    return prompt


def get_global_analysis_prompt(game_reviews: Dict[str, str], game_contexts: Dict[str, str]) -> str:
    """
    Generate prompt for global multi-game analysis.
    
    Args:
        game_reviews: Dict mapping match_ids to final coaching reviews
        game_contexts: Dict mapping match_ids to match context summaries
    
    Returns:
        Complete prompt string for global analysis
    """
    # Build the game summaries (simplified - just reviews, contexts are optional)
    game_summary = ""
    for idx, (match_id, review) in enumerate(game_reviews.items(), 1):
        context = game_contexts.get(match_id, "")
        if context and context.strip():
            game_summary += f"\nGAME {idx} ({match_id}):\n{context}\n\nREVIEW:\n{review}\n\n"
        else:
            game_summary += f"\nGAME {idx} ({match_id}):\n{review}\n\n"
    
    prompt = f"""{GLOBAL_ANALYSIS_PROMPT}

You have {len(game_reviews)} game(s) to analyze:

{game_summary}

Provide your multi-game analysis:"""
    
    return prompt


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

