"""
Main script for League of Legends match analysis pipeline.

This script:
1. Fetches games for a specified champion
2. Analyzes the first game using Claude AI
3. Converts the analysis to audio using ElevenLabs
"""
import argparse
import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

from find_champion_games import get_puuid_from_riot_id, find_champion_games
from make_analysis import analyze_match
from create_audio import text_to_speech, get_voice_id, VOICES

load_dotenv()


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Analyze League of Legends games and generate audio review",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using PUUID from .env file
  python main.py Lillia
  
  # Using Riot ID
  python main.py Lillia --game-name IPlayToWin10 --tag EUW
  
  # With custom voice and output
  python main.py Ashe --game-name Player --tag EUW --voice adam --output ashe_review.mp3
        """
    )
    
    parser.add_argument(
        "champion",
        help="Champion name to analyze (e.g., Lillia, Ashe, 'Lee Sin')"
    )
    
    parser.add_argument(
        "--game-name",
        help="Riot ID game name (e.g., IPlayToWin10). If not provided, uses PUUID from .env"
    )
    
    parser.add_argument(
        "--tag",
        default="EUW",
        help="Riot ID tag line (default: EUW)"
    )
    
    parser.add_argument(
        "--puuid",
        help="Player PUUID (overrides game-name/tag and .env)"
    )
    
    parser.add_argument(
        "--voice",
        default="george",
        choices=list(VOICES.keys()),
        help=f"Voice to use for audio (default: george). Available: {', '.join(VOICES.keys())}"
    )
    
    parser.add_argument(
        "--output",
        help="Output audio file name (default: {champion}_analysis.mp3)"
    )
    
    parser.add_argument(
        "--save-text",
        action="store_true",
        help="Also save the analysis as a text file"
    )
    
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="Skip fetching games (assumes champion folder already exists)"
    )
    
    parser.add_argument(
        "--num-games",
        type=int,
        default=2,
        help="Number of games to analyze (default: 2, analyzed in parallel)"
    )
    
    args = parser.parse_args()
    
    print("="*70)
    print("LOL ANALYZER - Match Review Generator")
    print("="*70)
    print(f"Champion: {args.champion}")
    print(f"Voice: {args.voice}")
    print("="*70 + "\n")
    
    # Step 1: Get PUUID
    puuid = None
    if args.puuid:
        puuid = args.puuid
        print(f"Using provided PUUID: {puuid[:20]}...")
    elif args.game_name:
        print(f"Getting PUUID for {args.game_name}#{args.tag}...")
        puuid = get_puuid_from_riot_id(args.game_name, args.tag)
        if not puuid:
            print("❌ Error: Could not find player with that Riot ID")
            sys.exit(1)
        print(f"✓ Found PUUID: {puuid[:20]}...")
    else:
        puuid = os.getenv("PUUID")
        if not puuid:
            print("❌ Error: No PUUID provided. Use --game-name/--tag or set PUUID in .env")
            sys.exit(1)
        print(f"Using PUUID from .env: {puuid[:20]}...")
    
    # Step 2: Fetch games (or use existing folder)
    champion_folder_name = args.champion.lower().replace(" ", "_").replace("'", "")
    champion_folder = Path(champion_folder_name)
    
    if args.no_fetch:
        print(f"\nSkipping game fetch (using existing {champion_folder}/ folder)")
        if not champion_folder.exists():
            print(f"❌ Error: Folder {champion_folder}/ does not exist!")
            sys.exit(1)
    else:
        print(f"\n{'='*70}")
        print(f"STEP 1: Fetching {args.champion} games")
        print('='*70)
        
        champion_games = find_champion_games(puuid, args.champion, save_to_folder=True)
        
        if not champion_games:
            print(f"\n❌ Error: No {args.champion} games found in latest 20 matches")
            sys.exit(1)
        
        print(f"\n✓ Found {len(champion_games)} {args.champion} game(s)")
    
    # Step 3: Get game files (up to num_games)
    print(f"\n{'='*70}")
    print(f"STEP 2: Loading game data ({args.num_games} game(s))")
    print('='*70)
    
    # Find log and timeline files
    log_files = sorted(champion_folder.glob("*_log.json"))
    
    # Exclude phase timeline files
    timeline_files = sorted([
        f for f in champion_folder.glob("*_timeline.json")
        if not any(x in f.name for x in ['_early', '_mid', '_late'])
    ])
    
    if not log_files or not timeline_files:
        print(f"❌ Error: No match files found in {champion_folder}/")
        sys.exit(1)
    
    # Limit to requested number of games
    num_to_analyze = min(args.num_games, len(log_files))
    log_files = log_files[:num_to_analyze]
    
    # Prepare match data
    matches_to_analyze = []
    for log_file in log_files:
        # Extract base filename (game_YYYYMMDD_XXXX) from log file
        base_filename = log_file.stem.replace("_log", "")
        timeline_file = champion_folder / f"{base_filename}_timeline.json"
        
        if not timeline_file.exists():
            print(f"⚠️  Timeline not found for {base_filename}, skipping")
            continue
        
        # Load match log to get match_id for analysis
        with open(log_file, 'r') as f:
            match_log = json.load(f)
        match_id = match_log.get("metadata", {}).get("matchId", base_filename)
        
        matches_to_analyze.append({
            'match_id': match_id,  # Keep for analysis reference
            'base_filename': base_filename,  # Use for file naming
            'log_file': log_file,
            'timeline_file': timeline_file
        })
    
    if not matches_to_analyze:
        print(f"❌ Error: No valid match pairs found")
        sys.exit(1)
    
    print(f"Found {len(matches_to_analyze)} game(s) to analyze:")
    for match in matches_to_analyze:
        print(f"  - {match['base_filename']}")
    
    # Step 4: Phase-based Analysis with Claude (PARALLEL for multiple games)
    print(f"\n{'='*70}")
    print(f"STEP 3: Phase-Based AI Analysis ({len(matches_to_analyze)} game(s) in PARALLEL)")
    print('='*70)
    
    import asyncio
    from make_analysis import analyze_match_async, synthesize_global_analysis
    
    # Async function to analyze multiple matches in parallel
    async def analyze_all_matches():
        tasks = []
        for match_info in matches_to_analyze:
            # Load match data
            with open(match_info['log_file'], 'r') as f:
                match_log = json.load(f)
            with open(match_info['timeline_file'], 'r') as f:
                timeline = json.load(f)
            
            # Create async task for this match
            task = analyze_match_async(
                match_log, timeline, puuid, 
                match_id=match_info['match_id']
            )
            tasks.append((match_info['base_filename'], match_info['match_id'], task))
        
        # Run all matches in parallel
        print(f"\n🚀 Launching {len(tasks)} game analyses in parallel...")
        print("  Each game will analyze 3 phases (early/mid/late) in parallel")
        print(f"  Total: {len(tasks)} × 3 = {len(tasks) * 3} parallel analyses!\n")
        
        results = await asyncio.gather(*[task for _, _, task in tasks])
        
        # Map results back to base filenames (for file naming) and match_ids (for reference)
        return {
            base_filename: (match_id, result) 
            for (base_filename, match_id, _), result in zip(tasks, results)
        }
    
    try:
        # Run parallel analysis
        all_results = asyncio.run(analyze_all_matches())
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Step 4.5: Generate global analysis if multiple games
    global_analysis = None
    if len(all_results) >= 2:
        print(f"\n{'='*70}")
        print("STEP 4: Global Multi-Game Analysis")
        print('='*70)
        try:
            # Convert results format for global analysis (it expects match_id -> result mapping)
            global_results = {match_id: result for _, (match_id, result) in all_results.items()}
            global_analysis = synthesize_global_analysis(global_results)
        except Exception as e:
            print(f"⚠️  Error during global analysis: {e}")
            print("Continuing with individual game outputs...")
    
    # Step 5: Save analyses and generate audio
    print(f"\n{'='*70}")
    print("STEP 5: Saving analyses and generating audio")
    print('='*70)
    
    audio_files = []
    for base_filename, (match_id, (match_context, phase_analyses, final_review)) in all_results.items():
        print(f"\nProcessing {base_filename}...")
        
        # Save analysis text if requested
        if args.save_text:
            context_file = champion_folder / f"{base_filename}_context.txt"
            with open(context_file, 'w') as f:
                f.write(match_context)
            print(f"  ✓ Context saved")
            
            # Save each phase analysis
            for phase_name, phase_analysis in phase_analyses.items():
                phase_file = champion_folder / f"{base_filename}_analysis_{phase_name}.txt"
                with open(phase_file, 'w') as f:
                    f.write(phase_analysis)
                print(f"  ✓ {phase_name.capitalize()} analysis saved")
            
            # Save final synthesized review
            review_file = champion_folder / f"{base_filename}_analysis_final.txt"
            with open(review_file, 'w') as f:
                f.write(final_review)
            print(f"  ✓ Final review saved")
        
        # Generate audio
        output_file = champion_folder / f"{base_filename}_analysis.mp3"
        
        try:
            voice_id = get_voice_id(args.voice)
            audio_file = text_to_speech(final_review, str(output_file), voice_id=voice_id)
            audio_files.append((base_filename, audio_file))
            print(f"  ✓ Audio generated: {audio_file}")
        except Exception as e:
            print(f"  ❌ Error during audio generation: {e}")
            continue
    
    # Save and generate audio for global analysis
    if global_analysis:
        print(f"\nProcessing GLOBAL ANALYSIS...")
        
        if args.save_text:
            global_file = champion_folder / f"{args.champion}_global_analysis.txt"
            with open(global_file, 'w') as f:
                f.write(global_analysis)
            print(f"  ✓ Global analysis saved")
        
        # Generate audio for global analysis
        global_audio_file = champion_folder / f"{args.champion}_global_analysis.mp3"
        
        try:
            voice_id = get_voice_id(args.voice)
            audio_file = text_to_speech(global_analysis, str(global_audio_file), voice_id=voice_id)
            audio_files.append(("GLOBAL", audio_file))
            print(f"  ✓ Global audio generated: {audio_file}")
        except Exception as e:
            print(f"  ⚠️  Error during global audio generation: {e}")
    
    # Final summary
    print(f"\n{'='*70}")
    print(f"✅ SUCCESS! {len(all_results)} Game(s) Analyzed!")
    print('='*70)
    print(f"Champion: {args.champion}")
    print(f"Games analyzed: {len(all_results)}")
    print(f"\nGenerated Files:")
    
    for base_filename, audio_file in audio_files:
        if base_filename == "GLOBAL":
            print(f"\n🌍 GLOBAL MULTI-GAME ANALYSIS:")
            print(f"  🎵 Audio: {audio_file}")
            if args.save_text:
                print(f"  📊 Text: {args.champion}_global_analysis.txt")
        else:
            print(f"\n📁 {base_filename}:")
            print(f"  🎵 Audio Review: {audio_file}")
            if args.save_text:
                _, (match_id, (match_context, phase_analyses, _)) = next(
                    (k, v) for k, v in all_results.items() if k == base_filename
                )
                print(f"  📊 Match Context: {base_filename}_context.txt")
                for phase_name in phase_analyses.keys():
                    print(f"  📝 {phase_name.capitalize()} Game: {base_filename}_analysis_{phase_name}.txt")
                print(f"  📝 Final Review: {base_filename}_analysis_final.txt")
    
    print(f"\nVoice used: {args.voice}")
    print(f"Analysis approach: Phase-based (Early → Mid → Late → Synthesis)")
    print(f"Parallelization: {len(all_results)} games × 3 phases = {len(all_results) * 3} parallel analyses")
    if global_analysis:
        print(f"Global analysis: ✅ Generated across all {len(all_results)} games")
    print(f"\n🚀 All {len(audio_files)} audio reviews ready to listen!")
    print('='*70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

