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


def apply_delta_encoding(timeline_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply delta encoding to participantFrames - only show stats that changed.
    For changed stats, show as "old_value -> new_value".
    
    Args:
        timeline_data: Timeline with full stats per frame
        
    Returns:
        Timeline with delta-encoded stats
    """
    frames = timeline_data.get("info", {}).get("frames", [])
    
    # Track previous stats for each participant
    previous_stats = {}
    
    for frame in frames:
        participant_frames = frame.get("participantFrames", {})
        
        for participant_key, participant_data in participant_frames.items():
            participant_id = participant_data.get("participantId")
            if not participant_id:
                continue
            
            # Get stats sections to check for changes
            current_stats = {}
            delta_encoded = {}
            
            # Copy non-stat fields as-is (but exclude participantId - it's replaced by championName/teamStartingSide)
            for key in ["championName", "teamStartingSide", "position"]:
                if key in participant_data:
                    delta_encoded[key] = participant_data[key]
            
            # Process main stats and nested objects
            for key, value in participant_data.items():
                if key in ["participantId", "championName", "teamStartingSide", "position"]:
                    continue  # Already handled or excluded
                
                if isinstance(value, dict):
                    # Handle nested objects like championStats, damageStats
                    nested_delta = {}
                    for nested_key, nested_value in value.items():
                        prev_nested = previous_stats.get(participant_id, {}).get(key, {}).get(nested_key)
                        
                        if prev_nested is None:
                            # First frame or new field
                            nested_delta[nested_key] = nested_value
                        elif prev_nested != nested_value:
                            # Value changed - show delta
                            nested_delta[nested_key] = f"{prev_nested} -> {nested_value}"
                        # If same, don't include it
                    
                    if nested_delta:  # Only include if there are changes
                        delta_encoded[key] = nested_delta
                    
                    # Store current for next iteration
                    if participant_id not in current_stats:
                        current_stats[participant_id] = {}
                    if key not in current_stats[participant_id]:
                        current_stats[participant_id][key] = {}
                    current_stats[participant_id][key] = value
                else:
                    # Handle simple values
                    prev_value = previous_stats.get(participant_id, {}).get(key)
                    
                    if prev_value is None:
                        # First frame
                        delta_encoded[key] = value
                    elif prev_value != value:
                        # Value changed
                        delta_encoded[key] = f"{prev_value} -> {value}"
                    # If same, don't include
                    
                    # Store current
                    if participant_id not in current_stats:
                        current_stats[participant_id] = {}
                    current_stats[participant_id][key] = value
            
            # Update the participant data with delta-encoded version
            participant_frames[participant_key] = delta_encoded
            
            # Update previous_stats for this participant
            if participant_id not in previous_stats:
                previous_stats[participant_id] = {}
            
            # Merge current stats into previous
            for key, value in participant_data.items():
                if key in ["participantId", "championName", "teamStartingSide", "position"]:
                    continue
                if isinstance(value, dict):
                    if key not in previous_stats[participant_id]:
                        previous_stats[participant_id][key] = {}
                    previous_stats[participant_id][key] = value.copy()
                else:
                    previous_stats[participant_id][key] = value
    
    return timeline_data


def add_champion_mapping(timeline_data: Dict[str, Any], match_log: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Add champion names and team sides directly into timeline data.
    
    Args:
        timeline_data: The timeline JSON data
        match_log: Optional match log to get champion names and teams
        
    Returns:
        Timeline data with champion names and team sides added inline
    """
    if not match_log:
        return timeline_data
    
    # Build mapping from puuid to champion name and team
    puuid_to_champion = {}
    puuid_to_team = {}
    participants_data = match_log.get("info", {}).get("participants", [])
    for participant in participants_data:
        puuid = participant.get("puuid")
        champion = participant.get("championName", "Unknown")
        team_id = participant.get("teamId", 0)
        if puuid:
            puuid_to_champion[puuid] = champion
            puuid_to_team[puuid] = team_id
    
    # Build mapping from participantId to champion name and team
    timeline_participants = timeline_data.get("info", {}).get("participants", [])
    participant_id_to_champion = {}
    participant_id_to_team = {}
    for participant in timeline_participants:
        participant_id = participant.get("participantId")
        puuid = participant.get("puuid")
        champion = puuid_to_champion.get(puuid, "Unknown")
        team_id = puuid_to_team.get(puuid, 0)
        if participant_id:
            participant_id_to_champion[participant_id] = champion
            participant_id_to_team[participant_id] = team_id
    
    # Add champion names and team sides inline throughout the timeline
    frames = timeline_data.get("info", {}).get("frames", [])
    for frame in frames:
        # Add to events with participantId
        for event in frame.get("events", []):
            if "participantId" in event:
                participant_id = event["participantId"]
                if participant_id in participant_id_to_champion:
                    event["championName"] = participant_id_to_champion[participant_id]
                if participant_id in participant_id_to_team:
                    event["teamStartingSide"] = "Blue" if participant_id_to_team[participant_id] == 100 else "Red"
                # Remove participantId after replacement
                del event["participantId"]
            # Also handle killerId, victimId, creatorId
            if "killerId" in event:
                killer_id = event["killerId"]
                if killer_id in participant_id_to_champion:
                    event["killerChampionName"] = participant_id_to_champion[killer_id]
                if killer_id in participant_id_to_team:
                    event["killerTeamStartingSide"] = "Blue" if participant_id_to_team[killer_id] == 100 else "Red"
            if "victimId" in event:
                victim_id = event["victimId"]
                if victim_id in participant_id_to_champion:
                    event["victimChampionName"] = participant_id_to_champion[victim_id]
                if victim_id in participant_id_to_team:
                    event["victimTeamStartingSide"] = "Blue" if participant_id_to_team[victim_id] == 100 else "Red"
            if "creatorId" in event:
                creator_id = event["creatorId"]
                if creator_id in participant_id_to_champion:
                    event["creatorChampionName"] = participant_id_to_champion[creator_id]
                if creator_id in participant_id_to_team:
                    event["creatorTeamStartingSide"] = "Blue" if participant_id_to_team[creator_id] == 100 else "Red"
        
        # Add to participantFrames
        participant_frames = frame.get("participantFrames", {})
        for frame_key, frame_data in participant_frames.items():
            if "participantId" in frame_data:
                participant_id = frame_data["participantId"]
                if participant_id in participant_id_to_champion:
                    frame_data["championName"] = participant_id_to_champion[participant_id]
                if participant_id in participant_id_to_team:
                    frame_data["teamStartingSide"] = "Blue" if participant_id_to_team[participant_id] == 100 else "Red"
                # Remove participantId after replacement
                del frame_data["participantId"]
    
    return timeline_data


def split_timeline_by_phases(
    timeline_data: Dict[str, Any],
    phases: Dict[str, Tuple[int, int]] = None,
    match_log: Dict[str, Any] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Split timeline data into game phases.
    
    Args:
        timeline_data: The full timeline data
        phases: Dictionary of phase names to (start_min, end_min) tuples
                If None, uses default GAME_PHASES
        match_log: Optional match log to add champion name mapping
        
    Returns:
        Dictionary mapping phase names to timeline data for that phase
    """
    if phases is None:
        phases = GAME_PHASES
    
    # Add champion mapping if match log provided
    if match_log:
        timeline_data = add_champion_mapping(timeline_data, match_log)
    
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
            },
            "participant_champions": timeline_data.get("participant_champions", {})
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

