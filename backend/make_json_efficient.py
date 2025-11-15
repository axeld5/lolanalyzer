#!/usr/bin/env python3
"""
Make JSON files sparse by removing zero/null/empty values.

This script processes JSON files (particularly match timeline data) and removes
unnecessary fields that contain zero, null, or empty values to reduce file size
and improve efficiency.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Union


def is_empty_value(value: Any) -> bool:
    """
    Check if a value should be considered "empty" and removed.
    
    Args:
        value: The value to check
        
    Returns:
        True if the value should be removed, False otherwise
    """
    # Check for None/null
    if value is None:
        return True
    
    # Check for zero (int or float)
    if isinstance(value, (int, float)) and value == 0:
        return True
    
    # Check for empty string
    if isinstance(value, str) and value == "":
        return True
    
    # Check for empty list
    if isinstance(value, list) and len(value) == 0:
        return True
    
    # Check for empty dict
    if isinstance(value, dict) and len(value) == 0:
        return True
    
    return False


def make_sparse(data: Any, keep_structure_keys: bool = False) -> Any:
    """
    Recursively remove empty values from a data structure.
    
    Args:
        data: The data structure to process (dict, list, or primitive)
        keep_structure_keys: If True, keep keys that are important for structure
                           (like 'participantId', 'timestamp', 'type', etc.)
        
    Returns:
        The sparse version of the data
    """
    # List of keys to always keep even if they're zero (important for structure)
    structural_keys = {
        'participantId', 'timestamp', 'type', 'level', 'itemId',
        'creatorId', 'killerId', 'victimId', 'position', 'x', 'y'
    }
    
    if isinstance(data, dict):
        sparse_dict = {}
        for key, value in data.items():
            # Always keep structural keys
            if key in structural_keys:
                sparse_dict[key] = make_sparse(value, keep_structure_keys)
            else:
                # Recursively process the value
                sparse_value = make_sparse(value, keep_structure_keys)
                # Only add if not empty
                if not is_empty_value(sparse_value):
                    sparse_dict[key] = sparse_value
        return sparse_dict
    
    elif isinstance(data, list):
        # Process each item in the list
        sparse_list = []
        for item in data:
            sparse_item = make_sparse(item, keep_structure_keys)
            # Keep all list items, even if they become empty dicts
            # (as they may represent important events/frames)
            sparse_list.append(sparse_item)
        return sparse_list
    
    else:
        # Primitive value, return as-is
        return data


def process_file(input_path: str, output_path: str = None) -> Dict[str, Any]:
    """
    Process a JSON file and create a sparse version.
    
    Args:
        input_path: Path to the input JSON file
        output_path: Path to save the sparse version (if None, adds '_sparse' suffix)
        
    Returns:
        Dictionary with statistics about the compression
    """
    # Read the input file
    print(f"Reading: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get original size
    original_size = os.path.getsize(input_path)
    
    # Make it sparse
    print("Making data sparse...")
    sparse_data = make_sparse(data)
    
    # Determine output path
    if output_path is None:
        path = Path(input_path)
        output_path = path.parent / f"{path.stem}_sparse{path.suffix}"
    
    # Write the sparse version
    print(f"Writing: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sparse_data, f, indent=2)
    
    # Get new size
    new_size = os.path.getsize(output_path)
    
    # Calculate statistics
    reduction = original_size - new_size
    reduction_percent = (reduction / original_size) * 100 if original_size > 0 else 0
    
    stats = {
        'input_file': input_path,
        'output_file': str(output_path),
        'original_size': original_size,
        'sparse_size': new_size,
        'reduction_bytes': reduction,
        'reduction_percent': reduction_percent
    }
    
    return stats


def format_bytes(bytes_value: int) -> str:
    """Format bytes into human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} TB"


def main():
    """Main function to process the match timeline file."""
    # Define the input file path
    script_dir = Path(__file__).parent
    input_file = script_dir / "old_files" / "match_timeline.json"
    
    if not input_file.exists():
        print(f"Error: File not found: {input_file}")
        return
    
    # Process the file
    print("=" * 70)
    print("JSON Sparse Optimization Tool")
    print("=" * 70)
    print()
    
    stats = process_file(str(input_file))
    
    # Display results
    print()
    print("=" * 70)
    print("Results:")
    print("=" * 70)
    print(f"Input file:       {stats['input_file']}")
    print(f"Output file:      {stats['output_file']}")
    print(f"Original size:    {format_bytes(stats['original_size'])}")
    print(f"Sparse size:      {format_bytes(stats['sparse_size'])}")
    print(f"Reduction:        {format_bytes(stats['reduction_bytes'])} ({stats['reduction_percent']:.2f}%)")
    print("=" * 70)
    
    # Show a sample comparison
    print()
    print("Sample - First participant frame (before):")
    with open(input_file, 'r') as f:
        original = json.load(f)
    print(json.dumps(original['info']['frames'][0]['participantFrames']['1']['damageStats'], indent=2))
    
    print()
    print("Sample - First participant frame (after):")
    with open(stats['output_file'], 'r') as f:
        sparse = json.load(f)
    damage_stats = sparse['info']['frames'][0]['participantFrames']['1'].get('damageStats', {})
    print(json.dumps(damage_stats, indent=2))
    print()


if __name__ == "__main__":
    main()

