#!/usr/bin/env python3
"""
Split timeline JSON files into game phases (early, mid, late).

This script takes a timeline file and splits it into game phases:
- Early game: 0-15 minutes
- Mid game: 15-30 minutes  
- Late game: 30+ minutes
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple


# Game phase definitions (in minutes)
GAME_PHASES = {
    "early": (0, 15),
    "mid": (15, 30),
    "late": (30, None)  # None means "until end of game"
}


def split_timeline_by_phases(
    timeline_data: Dict[str, Any],
    phases: Dict[str, Tuple[int, int]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Split timeline data into game phases.
    
    Args:
        timeline_data: The full timeline data
        phases: Dictionary of phase names to (start_min, end_min) tuples
                If None, uses default GAME_PHASES
        
    Returns:
        Dictionary mapping phase names to timeline data for that phase
    """
    if phases is None:
        phases = GAME_PHASES
    
    frames = timeline_data.get("info", {}).get("frames", [])
    
    if not frames:
        print("Warning: No frames found in timeline")
        return {}
    
    # Find the last timestamp to show game duration
    last_timestamp = 0
    for frame in frames:
        frame_timestamp = frame.get("timestamp", 0)
        if frame_timestamp > last_timestamp:
            last_timestamp = frame_timestamp
    
    game_duration_min = last_timestamp / 1000 / 60
    print(f"Game duration: {game_duration_min:.2f} minutes")
    print(f"Splitting into {len(phases)} phase(s): {', '.join(phases.keys())}")
    
    # Create phase data
    phase_data = {}
    
    for phase_name, (start_min, end_min) in phases.items():
        phase_start_ms = start_min * 60 * 1000
        # If end_min is None, use game end
        phase_end_ms = end_min * 60 * 1000 if end_min is not None else last_timestamp + 1
        
        # Filter frames for this phase
        phase_frames = []
        for frame in frames:
            frame_timestamp = frame.get("timestamp", 0)
            if phase_start_ms <= frame_timestamp < phase_end_ms:
                # Deep copy the frame and filter its events
                phase_frame = {
                    "events": [],
                    "participantFrames": frame.get("participantFrames", {}),
                    "timestamp": frame_timestamp
                }
                
                # Filter events that fall within this phase
                for event in frame.get("events", []):
                    event_timestamp = event.get("timestamp", 0)
                    if phase_start_ms <= event_timestamp < phase_end_ms:
                        phase_frame["events"].append(event)
                
                phase_frames.append(phase_frame)
        
        # Create phase data structure
        phase_timeline = {
            "metadata": timeline_data.get("metadata", {}),
            "info": {
                "endOfGameResult": timeline_data.get("info", {}).get("endOfGameResult", ""),
                "frameInterval": timeline_data.get("info", {}).get("frameInterval", 60000),
                "frames": phase_frames,
                "gameId": timeline_data.get("info", {}).get("gameId", 0),
                "participants": timeline_data.get("info", {}).get("participants", [])
            }
        }
        
        # Add phase metadata
        actual_end_min = end_min if end_min is not None else game_duration_min
        phase_timeline["phase_info"] = {
            "phase_name": phase_name,
            "phase_start_ms": phase_start_ms,
            "phase_end_ms": phase_end_ms,
            "phase_start_min": start_min,
            "phase_end_min": actual_end_min,
            "num_frames": len(phase_frames)
        }
        
        phase_data[phase_name] = phase_timeline
    
    return phase_data


def split_timeline_file(
    input_file: Path,
    output_dir: Path = None,
    phases: Dict[str, Tuple[int, int]] = None
) -> Dict[str, Path]:
    """
    Split a timeline file into phase files (early, mid, late).
    
    Args:
        input_file: Path to the input timeline JSON file
        output_dir: Directory to save phase files (default: same as input)
        phases: Custom phase definitions (default: GAME_PHASES)
        
    Returns:
        Dictionary mapping phase names to created file paths
    """
    print("="*70)
    print(f"Splitting Timeline by Phases: {input_file.name}")
    print("="*70)
    print(f"Input file: {input_file}")
    print()
    
    # Read the timeline file
    print("Reading timeline file...")
    with open(input_file, 'r', encoding='utf-8') as f:
        timeline_data = json.load(f)
    
    # Split into phases
    print("Splitting into game phases...")
    phase_data = split_timeline_by_phases(timeline_data, phases)
    
    if not phase_data:
        print("Error: No phases created")
        return {}
    
    # Determine output directory
    if output_dir is None:
        output_dir = input_file.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save each phase
    print()
    print("Saving phase files...")
    output_files = {}
    
    match_id = input_file.stem.replace("_timeline", "")
    
    for phase_name, phase_timeline in phase_data.items():
        phase_info = phase_timeline["phase_info"]
        start_min = int(phase_info["phase_start_min"])
        end_min = int(phase_info["phase_end_min"])
        
        output_filename = f"{match_id}_timeline_{phase_name}.json"
        output_path = output_dir / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(phase_timeline, f, indent=2)
        
        num_frames = phase_info["num_frames"]
        file_size_kb = output_path.stat().st_size / 1024
        
        print(f"  {phase_name.upper():6s} ({start_min:2d}-{end_min:2d} min): "
              f"{num_frames:3d} frames, {file_size_kb:7.2f} KB → {output_filename}")
        
        output_files[phase_name] = output_path
    
    return output_files


def main():
    """Main function."""
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    else:
        # Default to the specific file
        input_file = Path(__file__).parent / "lillia" / "EUW1_7601320835_timeline.json"
    
    if not input_file.exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    
    # Split the file into phases
    output_files = split_timeline_file(input_file)
    
    # Summary
    print()
    print("="*70)
    print(f"✅ Split complete! Created {len(output_files)} phase file(s)")
    print("="*70)
    print(f"Original file: {input_file}")
    print(f"Phase files saved to: {input_file.parent}/")
    print()
    
    total_size = sum(f.stat().st_size for f in output_files.values())
    print(f"Total size of phases: {total_size / 1024:.2f} KB")
    print(f"Original size: {input_file.stat().st_size / 1024:.2f} KB")
    print()
    print("Phases created:")
    for phase_name, file_path in output_files.items():
        print(f"  - {phase_name}: {file_path.name}")
    print()


if __name__ == "__main__":
    main()

