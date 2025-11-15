#!/usr/bin/env python3
"""
Count tokens in JSON files using tiktoken.

Usage:
    python count_tokens.py [file_path]
    
If no file path is provided, analyzes the default Lillia timeline file.
"""

import json
import sys
from pathlib import Path

try:
    import tiktoken
except ImportError:
    print("Error: tiktoken not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tiktoken"])
    import tiktoken


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens in text using tiktoken.
    
    Args:
        text: The text to count tokens for
        model: The model encoding to use (default: gpt-4)
        
    Returns:
        Number of tokens
    """
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def analyze_json_file(file_path: Path, model: str = "gpt-4"):
    """
    Analyze a JSON file and count its tokens.
    
    Args:
        file_path: Path to the JSON file
        model: Model encoding to use
    """
    print("="*70)
    print(f"Token Analysis: {file_path.name}")
    print("="*70)
    print(f"File: {file_path}")
    print(f"Model encoding: {model}")
    print()
    
    # Read the file
    print("Reading file...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    file_size = file_path.stat().st_size
    
    # Count tokens
    print("Counting tokens...")
    token_count = count_tokens(content, model)
    
    # Calculate statistics
    chars = len(content)
    tokens_per_kb = (token_count / file_size) * 1024 if file_size > 0 else 0
    chars_per_token = chars / token_count if token_count > 0 else 0
    
    print()
    print("="*70)
    print("Results:")
    print("="*70)
    print(f"File size:        {file_size:,} bytes ({file_size / 1024:.2f} KB)")
    print(f"Characters:       {chars:,}")
    print(f"Total tokens:     {token_count:,}")
    print(f"Tokens per KB:    {tokens_per_kb:.2f}")
    print(f"Chars per token:  {chars_per_token:.2f}")
    print("="*70)
    
    # Context window info
    print()
    print("Context Window Usage:")
    print(f"  • GPT-4 (8K):        {token_count / 8192 * 100:.1f}% of context")
    print(f"  • GPT-4 (32K):       {token_count / 32768 * 100:.1f}% of context")
    print(f"  • GPT-4 (128K):      {token_count / 131072 * 100:.1f}% of context")
    print(f"  • Claude 3.5 (200K): {token_count / 200000 * 100:.1f}% of context")
    print()
    
    return token_count


def main():
    """Main function."""
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    else:
        # Default to the specific file requested
        file_path = Path(__file__).parent / "lillia" / "game_20251114_x49l_timeline.json"
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    analyze_json_file(file_path)


if __name__ == "__main__":
    main()

