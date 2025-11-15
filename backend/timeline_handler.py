#!/usr/bin/env python3
"""
Handle timeline JSON processing: timestamp formatting and side detection.

This module processes timeline JSON files to:
- Add formatted timestamps (minute:seconds:milliseconds) to events
- Add isOnSide field (Red/Blue) based on position coordinates
"""

import json
from typing import Dict, List, Any, Optional


def format_timestamp(timestamp_ms: int) -> str:
    """
    Format timestamp in milliseconds to minute:seconds:milliseconds format.
    If > 60 minutes, still shows as minutes (e.g., 61:30:500).
    
    Args:
        timestamp_ms: Timestamp in milliseconds
        
    Returns:
        Formatted timestamp string (e.g., "5:30:500", "61:15:200")
    """
    total_seconds = timestamp_ms // 1000
    milliseconds = timestamp_ms % 1000
    
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    
    return f"{minutes}:{seconds:02d}:{milliseconds:03d}"


def determine_side_from_position(position: Dict[str, float]) -> Optional[str]:
    """
    Determine if a position is on Red or Blue side based on coordinates.
    
    League of Legends map coordinates:
    - Blue side (bottom-left): lower x and y values
    - Red side (top-right): higher x and y values
    - Map center is around (7000, 7000)
    - Blue base is around (0-2000, 0-2000)
    - Red base is around (12000-14000, 12000-14000)
    
    Args:
        position: Dict with 'x' and 'y' keys
        
    Returns:
        "Blue" or "Red" based on position, None if position is invalid
    """
    if not position or "x" not in position or "y" not in position:
        return None
    
    x = position.get("x", 0)
    y = position.get("y", 0)
    
    # Map center is approximately (7000, 7000)
    # Bottom-left (Blue side) has lower coordinates
    # Top-right (Red side) has higher coordinates
    # Using diagonal split: if x + y < 14000, likely Blue side
    # This is a simple heuristic - can be refined if needed
    
    # More precise: Blue side is bottom-left (lower x and y)
    # Red side is top-right (higher x and y)
    # Using sum of coordinates as a simple heuristic
    coordinate_sum = x + y
    
    # Threshold around map center (14000 = 2 * 7000)
    if coordinate_sum < 14000:
        return "Blue"
    else:
        return "Red"


def process_timeline_events(timeline_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process timeline events to add formatted timestamps and isOnSide fields.
    
    Args:
        timeline_data: The timeline JSON data
        
    Returns:
        Timeline data with processed events
    """
    frames = timeline_data.get("info", {}).get("frames", [])
    
    for frame in frames:
        events = frame.get("events", [])
        
        for event in events:
            # Add formatted timestamp
            if "timestamp" in event:
                timestamp_ms = event["timestamp"]
                event["formattedTimestamp"] = format_timestamp(timestamp_ms)
            
            # Add isOnSide based on position
            if "position" in event:
                position = event["position"]
                side = determine_side_from_position(position)
                if side:
                    event["isOnSide"] = side
    
    return timeline_data


def process_timeline_participant_frames(timeline_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process participant frames to add isOnSide fields based on position.
    
    Args:
        timeline_data: The timeline JSON data
        
    Returns:
        Timeline data with processed participant frames
    """
    frames = timeline_data.get("info", {}).get("frames", [])
    
    for frame in frames:
        participant_frames = frame.get("participantFrames", {})
        
        for participant_key, participant_data in participant_frames.items():
            if "position" in participant_data:
                position = participant_data["position"]
                side = determine_side_from_position(position)
                if side:
                    participant_data["isOnSide"] = side
    
    return timeline_data


def process_timeline(timeline_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process timeline JSON to add formatted timestamps and isOnSide fields.
    
    This function processes both events and participant frames.
    
    Args:
        timeline_data: The timeline JSON data
        
    Returns:
        Processed timeline data with timestamps and side information
    """
    # Process events
    timeline_data = process_timeline_events(timeline_data)
    
    # Process participant frames
    timeline_data = process_timeline_participant_frames(timeline_data)
    
    return timeline_data


def needs_processing(timeline_data: Dict[str, Any]) -> bool:
    """
    Check if a timeline needs processing (missing formattedTimestamp or isOnSide).
    
    Args:
        timeline_data: The timeline JSON data
        
    Returns:
        True if processing is needed, False otherwise
    """
    frames = timeline_data.get("info", {}).get("frames", [])
    
    # Check first few events and participant frames
    for frame in frames[:5]:  # Check first 5 frames
        # Check events
        for event in frame.get("events", [])[:3]:  # Check first 3 events
            if "timestamp" in event and "formattedTimestamp" not in event:
                return True
            if "position" in event and "isOnSide" not in event:
                return True
        
        # Check participant frames
        for participant_data in frame.get("participantFrames", {}).values():
            if "position" in participant_data and "isOnSide" not in participant_data:
                return True
    
    return False


def ensure_timeline_processed(timeline_data: Dict[str, Any], timeline_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Ensure timeline is processed (add formattedTimestamp and isOnSide if missing).
    Optionally saves to file if provided.
    
    Args:
        timeline_data: The timeline JSON data
        timeline_file: Optional path to save processed timeline
        
    Returns:
        Processed timeline data
    """
    if needs_processing(timeline_data):
        timeline_data = process_timeline(timeline_data)
        
        # Save if file path provided
        if timeline_file:
            with open(timeline_file, 'w', encoding='utf-8') as f:
                json.dump(timeline_data, f, indent=2)
            print(f"✓ Timeline processed and saved to {timeline_file}")
    
    return timeline_data


def process_timeline_file(input_file: str, output_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a timeline JSON file and optionally save the result.
    
    Args:
        input_file: Path to input timeline JSON file
        output_file: Optional path to save processed timeline (if None, overwrites input)
        
    Returns:
        Processed timeline data
    """
    # Read the timeline file
    with open(input_file, 'r', encoding='utf-8') as f:
        timeline_data = json.load(f)
    
    # Process the timeline
    processed_timeline = process_timeline(timeline_data)
    
    # Save if output file specified
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_timeline, f, indent=2)
        print(f"Processed timeline saved to {output_file}")
    else:
        # Overwrite input file
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(processed_timeline, f, indent=2)
        print(f"Processed timeline saved to {input_file}")
    
    return processed_timeline


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    if len(sys.argv) < 2:
        print("Usage: python timeline_handler.py <timeline_file> [output_file]")
        print("Example: python timeline_handler.py lillia/game_20251112_1GHT_timeline.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(input_file).exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    
    process_timeline_file(input_file, output_file)
    print("✓ Timeline processing complete!")

