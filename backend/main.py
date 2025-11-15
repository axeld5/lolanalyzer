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
    
    # Step 3: Get the first game files
    print(f"\n{'='*70}")
    print("STEP 2: Loading first game data")
    print('='*70)
    
    # Find the first log and timeline files
    log_files = sorted(champion_folder.glob("*_log.json"))
    timeline_files = sorted(champion_folder.glob("*_timeline.json"))
    
    if not log_files or not timeline_files:
        print(f"❌ Error: No match files found in {champion_folder}/")
        sys.exit(1)
    
    log_file = log_files[0]
    # Find matching timeline
    match_id = log_file.stem.replace("_log", "")
    timeline_file = champion_folder / f"{match_id}_timeline.json"
    
    if not timeline_file.exists():
        print(f"❌ Error: Timeline file not found: {timeline_file}")
        sys.exit(1)
    
    print(f"Match ID: {match_id}")
    print(f"Log file: {log_file}")
    print(f"Timeline file: {timeline_file}")
    
    # Step 4: Phase-based Analysis with Claude
    print(f"\n{'='*70}")
    print("STEP 3: Phase-Based AI Analysis with Claude")
    print('='*70)
    
    import json
    with open(log_file, 'r') as f:
        match_log = json.load(f)
    with open(timeline_file, 'r') as f:
        timeline = json.load(f)
    
    try:
        match_context, phase_analyses, final_review = analyze_match(match_log, timeline, puuid)
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        sys.exit(1)
    
    # Save analysis text if requested
    if args.save_text:
        context_file = champion_folder / f"{match_id}_context.txt"
        with open(context_file, 'w') as f:
            f.write(match_context)
        print(f"✓ Context saved to {context_file}")
        
        # Save each phase analysis
        for phase_name, phase_analysis in phase_analyses.items():
            phase_file = champion_folder / f"{match_id}_analysis_{phase_name}.txt"
            with open(phase_file, 'w') as f:
                f.write(phase_analysis)
            print(f"✓ {phase_name.capitalize()} analysis saved to {phase_file}")
        
        # Save final synthesized review
        review_file = champion_folder / f"{match_id}_analysis_final.txt"
        with open(review_file, 'w') as f:
            f.write(final_review)
        print(f"✓ Final review saved to {review_file}")
    
    # Step 5: Convert final review to audio
    print(f"\n{'='*70}")
    print("STEP 4: Converting coaching review to audio")
    print('='*70)
    
    output_file = args.output
    if not output_file:
        output_file = champion_folder / f"{match_id}_analysis.mp3"
    
    try:
        voice_id = get_voice_id(args.voice)
        audio_file = text_to_speech(final_review, str(output_file), voice_id=voice_id)
    except Exception as e:
        print(f"❌ Error during audio generation: {e}")
        sys.exit(1)
    
    # Final summary
    print(f"\n{'='*70}")
    print("✅ SUCCESS! Phase-Based Analysis Complete")
    print('='*70)
    print(f"Champion: {args.champion}")
    print(f"Match ID: {match_id}")
    print(f"\nGenerated Files:")
    print(f"  🎵 Audio Review: {audio_file}")
    if args.save_text:
        print(f"  📊 Match Context: {context_file}")
        for phase_name in phase_analyses.keys():
            phase_file = champion_folder / f"{match_id}_analysis_{phase_name}.txt"
            print(f"  📝 {phase_name.capitalize()} Game: {phase_file}")
        print(f"  📝 Final Review: {review_file}")
    print(f"\nVoice used: {args.voice}")
    print(f"Analysis approach: Phase-based (Early → Mid → Late → Synthesis)")
    print(f"Phases analyzed: {', '.join(phase_analyses.keys())}")
    print("\nYou can now listen to your match review!")
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

