"""
Module for analyzing League of Legends matches using Claude AI.
Uses multi-stage phase-based analysis:
1. Stage 1: Analyze match log for context and stats
2. Stage 2-4: Analyze each game phase (early, mid, late) IN PARALLEL
3. Stage 5: Synthesize all phases into final coaching review
"""
import anthropic
import os
import json
import asyncio
from dotenv import load_dotenv
from typing import Optional, Tuple, Dict
from pathlib import Path
from prompt import get_match_log_prompt, get_phase_prompt, get_synthesis_prompt, get_global_analysis_prompt, get_single_pass_analysis_prompt
from split_timeline import split_timeline_by_phases, GAME_PHASES
from timeline_handler import process_timeline, ensure_timeline_processed

load_dotenv()


def analyze_match_log(match_log: dict, player_puuid: str,
                      model: str = "claude-sonnet-4-5") -> str:
    """
    Stage 1: Analyze match log to extract game context and player performance.
    
    Args:
        match_log: The match log JSON data
        player_puuid: The PUUID of the player to analyze
        model: The Claude model to use
    
    Returns:
        Structured analysis summary for feeding into timeline analysis
    """
    print("=" * 70)
    print("STAGE 1: Analyzing Match Log (Stats & Context)")
    print("=" * 70)
    
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    print("Generating match log analysis prompt...")
    prompt = get_match_log_prompt(match_log, player_puuid)
    
    print(f"Sending match log to Claude ({model})...")
    print("Extracting game context, player stats, and key insights...")
    
    try:
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        context_summary = message.content[0].text
        print("✓ Match log analysis complete!")
        print(f"  - Generated {len(context_summary)} character context summary")
        return context_summary
        
    except Exception as e:
        print(f"❌ Error during match log analysis: {e}")
        raise


async def analyze_phase_async(phase_name: str, phase_timeline: dict, match_context: str,
                              player_puuid: str, champion_name: str,
                              model: str = "claude-sonnet-4-5") -> str:
    """
    Analyze a specific game phase (early, mid, or late) asynchronously.
    
    Args:
        phase_name: Name of the phase ("early", "mid", or "late")
        phase_timeline: The timeline JSON data for this phase
        match_context: The summary from Stage 1
        player_puuid: The PUUID of the player to analyze
        champion_name: The champion name
        model: The Claude model to use
    
    Returns:
        Phase-specific analysis text
    """
    print(f"  Starting {phase_name.upper()} game phase analysis...")
    
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    prompt = get_phase_prompt(phase_name, phase_timeline, match_context,
                              player_puuid, champion_name)
    
    try:
        # Run the synchronous API call in an executor
        loop = asyncio.get_event_loop()
        message = await loop.run_in_executor(
            None,
            lambda: client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
        )
        
        phase_analysis = message.content[0].text
        print(f"  ✓ {phase_name.capitalize()} game analysis complete! ({len(phase_analysis)} chars)")
        return phase_analysis
        
    except Exception as e:
        print(f"  ❌ Error during {phase_name} game analysis: {e}")
        raise


def synthesize_final_review(match_context: str, phase_analyses: dict,
                            champion_name: str,
                            model: str = "claude-sonnet-4-5") -> str:
    """
    Synthesize all phase analyses into a cohesive final coaching review.
    
    Args:
        match_context: The summary from Stage 1
        phase_analyses: Dict of phase analyses {"early": "...", "mid": "...", "late": "..."}
        champion_name: The champion name
        model: The Claude model to use
    
    Returns:
        Final synthesized coaching review
    """
    print("\n" + "=" * 70)
    print("FINAL STAGE: Synthesizing Coaching Review")
    print("=" * 70)
    
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    print("Generating synthesis prompt...")
    prompt = get_synthesis_prompt(match_context, phase_analyses, champion_name)
    
    print(f"Sending all analyses to Claude ({model}) for final synthesis...")
    print("Creating cohesive coaching narrative...")
    
    try:
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        final_review = message.content[0].text
        print("✓ Final synthesis complete!")
        print(f"  - Generated {len(final_review)} character final review")
        return final_review
        
    except Exception as e:
        print(f"❌ Error during final synthesis: {e}")
        raise


async def analyze_match_single_pass_async(match_log: dict, timeline: dict, player_puuid: str,
                                          model: str = "claude-sonnet-4-5", match_id: str = "Unknown") -> Tuple[str, Dict[str, str], str]:
    """
    Single-pass match analysis using Claude AI (processes log + timeline in one go).
    
    This method processes the entire game in a single analysis pass, using the processed
    timeline with formatted timestamps and isOnSide fields.
    
    Args:
        match_log: The match log JSON data
        timeline: The timeline JSON data (will be processed with timeline_handler)
        player_puuid: The PUUID of the player to analyze
        model: The Claude model to use (default: Claude sonnet 4.5)
        match_id: Optional match ID for logging
    
    Returns:
        Tuple of (empty_string, empty_dict, final_review)
        - Returns empty strings/dicts for compatibility with phase-based method
        - final_review: Complete coaching review from single-pass analysis
    """
    # Extract champion name
    participants = match_log.get("info", {}).get("participants", [])
    champion_name = "Unknown"
    for participant in participants:
        if participant.get("puuid") == player_puuid:
            champion_name = participant.get("championName", "Unknown")
            break
    
    print("\n" + "=" * 70)
    print(f"SINGLE-PASS ANALYSIS - {match_id}")
    print("=" * 70)
    print(f"Champion: {champion_name}")
    print(f"Model: {model}")
    print("=" * 70)
    
    # Ensure timeline is processed (add formatted timestamps and isOnSide if missing)
    print("\nEnsuring timeline is processed (adding timestamps and isOnSide if needed)...")
    processed_timeline = ensure_timeline_processed(timeline)
    print("✓ Timeline ready")
    
    # Generate prompt
    print("\nGenerating single-pass analysis prompt...")
    prompt = get_single_pass_analysis_prompt(match_log, processed_timeline, player_puuid, champion_name)
    
    # Call Claude API
    print(f"Sending match data to Claude ({model}) for comprehensive analysis...")
    print("Analyzing entire game in one pass...")
    
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    try:
        loop = asyncio.get_event_loop()
        message = await loop.run_in_executor(
            None,
            lambda: client.beta.messages.create(
                model=model,
                max_tokens=1024,
                betas=["context-1m-2025-08-07"],
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
        )
        
        final_review = message.content[0].text
        print("✓ Single-pass analysis complete!")
        print(f"  - Generated {len(final_review)} character coaching review")
        
        print("\n" + "=" * 70)
        print(f"✅ ANALYSIS COMPLETE - {match_id}")
        print("=" * 70)
        print(f"Final Review: {len(final_review)} characters")
        print("=" * 70)
        
        # Return empty strings/dicts for compatibility with phase-based method
        return "", {}, final_review
        
    except Exception as e:
        print(f"❌ Error during single-pass analysis: {e}")
        raise


async def analyze_match_async(match_log: dict, timeline: dict, player_puuid: str, 
                              model: str = "claude-sonnet-4-5", match_id: str = "Unknown",
                              use_single_pass: bool = True) -> Tuple[str, Dict[str, str], str]:
    """
    Match analysis using Claude AI (ASYNC VERSION).
    
    Can use either:
    - Single-pass analysis (default): Processes log + timeline in one go
    - Phase-based analysis: Multi-stage pipeline (global -> early/mid/late -> full)
    
    Args:
        match_log: The match log JSON data
        timeline: The timeline JSON data
        player_puuid: The PUUID of the player to analyze
        model: The Claude model to use (default: Claude sonnet 4.5)
        match_id: Optional match ID for logging
        use_single_pass: If True (default), use single-pass analysis. If False, use phase-based pipeline.
    
    Returns:
        Tuple of (match_context, phase_analyses, final_review)
        - match_context: Summary from Stage 1 (empty string for single-pass)
        - phase_analyses: Dict of phase analyses {"early": "...", "mid": "...", "late": "..."} (empty dict for single-pass)
        - final_review: Complete coaching review
    """
    # Use single-pass analysis by default
    if use_single_pass:
        return await analyze_match_single_pass_async(match_log, timeline, player_puuid, model, match_id)
    
    # Otherwise use phase-based analysis
    return await analyze_match_phase_based_async(match_log, timeline, player_puuid, model, match_id)


async def analyze_match_phase_based_async(match_log: dict, timeline: dict, player_puuid: str, 
                                          model: str = "claude-sonnet-4-5", match_id: str = "Unknown") -> Tuple[str, Dict[str, str], str]:
    """
    Multi-stage phase-based match analysis using Claude AI (ASYNC VERSION).
    
    Stage 1: Analyze match log for context and stats
    Stage 2-4: Analyze each game phase (early, mid, late) in parallel
    Stage 5: Synthesize all phases into final coaching review
    
    Args:
        match_log: The match log JSON data
        timeline: The timeline JSON data
        player_puuid: The PUUID of the player to analyze
        model: The Claude model to use (default: Claude sonnet 4.5)
        match_id: Optional match ID for logging
    
    Returns:
        Tuple of (match_context, phase_analyses, final_review)
        - match_context: Summary from Stage 1
        - phase_analyses: Dict of phase analyses {"early": "...", "mid": "...", "late": "..."}
        - final_review: Synthesized spoken coaching review from final stage
    """
    # Extract champion name
    participants = match_log.get("info", {}).get("participants", [])
    champion_name = "Unknown"
    for participant in participants:
        if participant.get("puuid") == player_puuid:
            champion_name = participant.get("championName", "Unknown")
            break
    
    print("\n" + "=" * 70)
    print(f"PHASE-BASED ANALYSIS PIPELINE - {match_id}")
    print("=" * 70)
    print(f"Champion: {champion_name}")
    print(f"Model: {model}")
    print(f"Phases: {', '.join(GAME_PHASES.keys())}")
    print("=" * 70)
    
    # Stage 1: Match Log Analysis
    print("\n" + "=" * 70)
    print(f"STAGE 1: Match Context Analysis - {match_id}")
    print("=" * 70)
    match_context = analyze_match_log(match_log, player_puuid, model)
    
    # Split timeline into phases (with champion mapping)
    print("\n" + "=" * 70)
    print(f"STAGE 2-4: Phase-by-Phase Analysis (PARALLEL) - {match_id}")
    print("=" * 70)
    print("Splitting timeline into game phases with champion mapping...")
    phase_timelines = split_timeline_by_phases(timeline, match_log=match_log)
    
    # Analyze each phase in parallel using asyncio
    print("Launching parallel phase analyses...")
    
    tasks = []
    phase_names = []
    
    for phase_name in ["early", "mid", "late"]:
        if phase_name in phase_timelines:
            phase_timeline = phase_timelines[phase_name]
            task = analyze_phase_async(
                phase_name, phase_timeline, match_context,
                player_puuid, champion_name, model
            )
            tasks.append(task)
            phase_names.append(phase_name)
        else:
            print(f"  ⚠️  {phase_name.capitalize()} phase not found (game may have ended early)")
    
    # Run all phases in parallel
    results = await asyncio.gather(*tasks)
    
    # Map results back to phase names
    phase_analyses = {phase_name: result for phase_name, result in zip(phase_names, results)}
    
    # Final Stage: Synthesis
    print(f"\n{'='*70}")
    print(f"FINAL STAGE: Synthesizing Review - {match_id}")
    print('='*70)
    final_review = synthesize_final_review(
        match_context, phase_analyses, champion_name, model
    )
    
    print("\n" + "=" * 70)
    print(f"✅ ANALYSIS COMPLETE - {match_id}")
    print("=" * 70)
    print(f"Stage 1 (Context): {len(match_context)} characters")
    for phase_name, analysis in phase_analyses.items():
        print(f"Stage {list(phase_analyses.keys()).index(phase_name) + 2} ({phase_name.capitalize()}): {len(analysis)} characters")
    print(f"Final Stage (Synthesis): {len(final_review)} characters")
    print("=" * 70)
    
    return match_context, phase_analyses, final_review


def analyze_match(match_log: dict, timeline: dict, player_puuid: str, 
                  model: str = "claude-sonnet-4-5", use_single_pass: bool = True) -> Tuple[str, Dict[str, str], str]:
    """
    Synchronous wrapper for analyze_match_async for backwards compatibility.
    
    Args:
        match_log: The match log JSON data
        timeline: The timeline JSON data
        player_puuid: The PUUID of the player to analyze
        model: The Claude model to use
        use_single_pass: If True (default), use single-pass analysis. If False, use phase-based pipeline.
    
    Returns:
        Tuple of (match_context, phase_analyses, final_review)
    """
    return asyncio.run(analyze_match_async(match_log, timeline, player_puuid, model, match_id="Unknown", use_single_pass=use_single_pass))


def analyze_match_from_files(log_file: str, timeline_file: str, player_puuid: str, use_single_pass: bool = True) -> Tuple[str, Dict[str, str], str]:
    """
    Analyze a match by loading data from JSON files.
    
    Args:
        log_file: Path to the match log JSON file
        timeline_file: Path to the timeline JSON file
        player_puuid: The PUUID of the player to analyze
        use_single_pass: If True (default), use single-pass analysis. If False, use phase-based pipeline.
    
    Returns:
        Tuple of (match_context, phase_analyses, final_review)
    """
    print(f"Loading match log from {log_file}...")
    with open(log_file, 'r') as f:
        match_log = json.load(f)
    
    print(f"Loading timeline from {timeline_file}...")
    with open(timeline_file, 'r') as f:
        timeline = json.load(f)
    
    # Ensure timeline is processed (has formattedTimestamp and isOnSide)
    timeline = ensure_timeline_processed(timeline, str(timeline_file))
    
    return analyze_match(match_log, timeline, player_puuid, use_single_pass=use_single_pass)


def synthesize_global_analysis(all_results: Dict[str, Tuple[str, Dict[str, str], str]],
                               model: str = "claude-sonnet-4-5") -> str:
    """
    Create a comprehensive analysis across all analyzed games.
    
    Args:
        all_results: Dict mapping match_ids to (context, phase_analyses, final_review) tuples
        model: The Claude model to use
    
    Returns:
        Global multi-game analysis text
    """
    if len(all_results) < 2:
        print(f"⚠️  Only {len(all_results)} game(s) analyzed, skipping global analysis (need at least 2)")
        return ""
    
    print("\n" + "=" * 70)
    print(f"GLOBAL ANALYSIS: Synthesizing {len(all_results)} Games")
    print("=" * 70)
    
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Extract contexts and reviews
    # Note: For single-pass analysis, contexts may be empty strings
    game_contexts = {match_id: result[0] for match_id, result in all_results.items()}
    game_reviews = {match_id: result[2] for match_id, result in all_results.items()}
    
    # Debug: Print what we're analyzing
    print(f"Analyzing {len(game_reviews)} game reviews...")
    
    print("Generating global analysis prompt...")
    prompt = get_global_analysis_prompt(game_reviews, game_contexts)
    
    print(f"Sending all game data to Claude ({model}) for comprehensive analysis...")
    print("Identifying patterns, trends, and priority improvements across all games...")
    
    try:
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        global_analysis = message.content[0].text
        print("✓ Global multi-game analysis complete!")
        print(f"  - Generated {len(global_analysis)} character comprehensive summary")
        return global_analysis
        
    except Exception as e:
        print(f"❌ Error during global analysis: {e}")
        raise


def save_analysis(analysis: str, output_file: str) -> None:
    """
    Save analysis text to a file.
    
    Args:
        analysis: The analysis text
        output_file: Path to save the analysis
    """
    with open(output_file, 'w') as f:
        f.write(analysis)
    print(f"✓ Analysis saved to {output_file}")


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python make_analysis.py <log_file> <timeline_file> <player_puuid>")
        print("Example: python make_analysis.py lillia/EUW1_123_log.json lillia/EUW1_123_timeline.json <puuid>")
        sys.exit(1)
    
    log_file = sys.argv[1]
    timeline_file = sys.argv[2]
    player_puuid = sys.argv[3]
    
    try:
        match_context, phase_analyses, final_review = analyze_match_from_files(log_file, timeline_file, player_puuid)
        
        print("\n" + "="*60)
        print("STAGE 1: MATCH CONTEXT")
        print("="*60)
        print(match_context)
        
        for phase_name, phase_analysis in phase_analyses.items():
            print("\n" + "="*60)
            print(f"STAGE: {phase_name.upper()} GAME ANALYSIS")
            print("="*60)
            print(phase_analysis)
        
        print("\n" + "="*60)
        print("FINAL: SYNTHESIZED COACHING REVIEW")
        print("="*60)
        print(final_review)
        print("="*60)
        
        # Save all files
        context_file = "analysis_context.txt"
        save_analysis(match_context, context_file)
        
        for phase_name, phase_analysis in phase_analyses.items():
            phase_file = f"analysis_{phase_name}.txt"
            save_analysis(phase_analysis, phase_file)
        
        review_file = "analysis_review.txt"
        save_analysis(final_review, review_file)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

