"""
Module for analyzing League of Legends matches using Claude AI.
Uses multi-stage phase-based analysis:
1. Stage 1: Analyze match log for context and stats
2. Stage 2-4: Analyze each game phase (early, mid, late) separately
3. Stage 5: Synthesize all phases into final coaching review
"""
import anthropic
import os
import json
from dotenv import load_dotenv
from typing import Optional, Tuple, Dict
from pathlib import Path
from prompt import get_match_log_prompt, get_phase_prompt, get_synthesis_prompt
from split_timeline import split_timeline_by_phases, GAME_PHASES

load_dotenv()


def analyze_match_log(match_log: dict, player_puuid: str,
                      model: str = "claude-haiku-4-5") -> str:
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


def analyze_phase(phase_name: str, phase_timeline: dict, match_context: str,
                  previous_analyses: dict, player_puuid: str, champion_name: str,
                  model: str = "claude-haiku-4-5") -> str:
    """
    Analyze a specific game phase (early, mid, or late).
    
    Args:
        phase_name: Name of the phase ("early", "mid", or "late")
        phase_timeline: The timeline JSON data for this phase
        match_context: The summary from Stage 1
        previous_analyses: Dict of previous phase analyses
        player_puuid: The PUUID of the player to analyze
        champion_name: The champion name
        model: The Claude model to use
    
    Returns:
        Phase-specific analysis text
    """
    print(f"\nAnalyzing {phase_name.upper()} game phase...")
    
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    prompt = get_phase_prompt(phase_name, phase_timeline, match_context,
                              previous_analyses, player_puuid, champion_name)
    
    print(f"  Sending {phase_name} game data to Claude ({model})...")
    
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
        
        phase_analysis = message.content[0].text
        print(f"  ✓ {phase_name.capitalize()} game analysis complete!")
        print(f"    Generated {len(phase_analysis)} characters")
        return phase_analysis
        
    except Exception as e:
        print(f"  ❌ Error during {phase_name} game analysis: {e}")
        raise


def synthesize_final_review(match_context: str, phase_analyses: dict,
                            champion_name: str,
                            model: str = "claude-haiku-4-5") -> str:
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


def analyze_match(match_log: dict, timeline: dict, player_puuid: str, 
                  model: str = "claude-haiku-4-5") -> Tuple[str, Dict[str, str], str]:
    """
    Multi-stage phase-based match analysis using Claude AI.
    
    Stage 1: Analyze match log for context and stats
    Stage 2-4: Analyze each game phase (early, mid, late) separately
    Stage 5: Synthesize all phases into final coaching review
    
    Args:
        match_log: The match log JSON data
        timeline: The timeline JSON data
        player_puuid: The PUUID of the player to analyze
        model: The Claude model to use (default: Claude haiku 4.5)
    
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
    print("PHASE-BASED ANALYSIS PIPELINE")
    print("=" * 70)
    print(f"Champion: {champion_name}")
    print(f"Model: {model}")
    print(f"Phases: {', '.join(GAME_PHASES.keys())}")
    print("=" * 70)
    
    # Stage 1: Match Log Analysis
    print("\n" + "=" * 70)
    print("STAGE 1: Match Context Analysis")
    print("=" * 70)
    match_context = analyze_match_log(match_log, player_puuid, model)
    
    # Split timeline into phases
    print("\n" + "=" * 70)
    print("STAGE 2-4: Phase-by-Phase Timeline Analysis")
    print("=" * 70)
    print("Splitting timeline into game phases...")
    phase_timelines = split_timeline_by_phases(timeline)
    
    # Analyze each phase in order
    phase_analyses = {}
    for phase_name in ["early", "mid", "late"]:
        if phase_name in phase_timelines:
            phase_timeline = phase_timelines[phase_name]
            phase_analysis = analyze_phase(
                phase_name, phase_timeline, match_context,
                phase_analyses, player_puuid, champion_name, model
            )
            phase_analyses[phase_name] = phase_analysis
        else:
            print(f"  ⚠️  {phase_name.capitalize()} phase not found (game may have ended early)")
    
    # Final Stage: Synthesis
    final_review = synthesize_final_review(
        match_context, phase_analyses, champion_name, model
    )
    
    print("\n" + "=" * 70)
    print("✅ PHASE-BASED ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"Stage 1 (Context): {len(match_context)} characters")
    for phase_name, analysis in phase_analyses.items():
        print(f"Stage {list(phase_analyses.keys()).index(phase_name) + 2} ({phase_name.capitalize()}): {len(analysis)} characters")
    print(f"Final Stage (Synthesis): {len(final_review)} characters")
    print("=" * 70)
    
    return match_context, phase_analyses, final_review


def analyze_match_from_files(log_file: str, timeline_file: str, player_puuid: str) -> Tuple[str, Dict[str, str], str]:
    """
    Analyze a match by loading data from JSON files (phase-based process).
    
    Args:
        log_file: Path to the match log JSON file
        timeline_file: Path to the timeline JSON file
        player_puuid: The PUUID of the player to analyze
    
    Returns:
        Tuple of (match_context, phase_analyses, final_review)
    """
    print(f"Loading match log from {log_file}...")
    with open(log_file, 'r') as f:
        match_log = json.load(f)
    
    print(f"Loading timeline from {timeline_file}...")
    with open(timeline_file, 'r') as f:
        timeline = json.load(f)
    
    return analyze_match(match_log, timeline, player_puuid)


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

