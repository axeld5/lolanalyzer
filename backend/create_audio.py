"""
Module for converting text to speech using ElevenLabs.
"""
from elevenlabs import ElevenLabs
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()


def text_to_speech(text: str, output_file: str = "analysis.mp3",
                   voice_id: str = "JBFqnCBsd6RMkjVDRZzb",
                   model_id: str = "eleven_multilingual_v2") -> str:
    """
    Convert text to speech using ElevenLabs API.
    
    Args:
        text: The text to convert to speech
        output_file: Path to save the audio file (default: analysis.mp3)
        voice_id: ElevenLabs voice ID to use (default: George)
        model_id: ElevenLabs model to use
    
    Returns:
        Path to the generated audio file
    """
    print("Initializing ElevenLabs API...")
    client = ElevenLabs(
        base_url="https://api.elevenlabs.io",
        api_key=os.getenv("ELEVENLABS_API_KEY")
    )
    
    print(f"Converting text to speech (voice: {voice_id})...")
    print("This may take a moment...")
    
    try:
        audio_stream = client.text_to_speech.convert(
            voice_id=voice_id,
            output_format="mp3_44100_128",
            text=text,
            model_id=model_id
        )
        
        print(f"Saving audio to {output_file}...")
        with open(output_file, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)
        
        print(f"✓ Audio saved to {output_file}")
        return output_file
        
    except Exception as e:
        print(f"Error during text-to-speech conversion: {e}")
        raise


def analyze_text_to_speech_from_file(text_file: str, output_file: str = "analysis.mp3") -> str:
    """
    Convert a text file to speech.
    
    Args:
        text_file: Path to the text file
        output_file: Path to save the audio file
    
    Returns:
        Path to the generated audio file
    """
    print(f"Loading text from {text_file}...")
    with open(text_file, 'r') as f:
        text = f.read()
    
    return text_to_speech(text, output_file)


# Available voices (you can customize this)
VOICES = {
    "george": "JBFqnCBsd6RMkjVDRZzb",  # Default - clear, professional
    "adam": "pNInz6obpgDQGcFmaJgB",    # Deep, authoritative
    "bill": "pqHfZKP75CvOlQylNhV4",    # Warm, friendly
    "callum": "N2lVS1w4EtoT3dr4eOWO",  # Young, energetic
    "charlie": "IKne3meq5aSn9XLyUdCD",  # British, natural
}


def get_voice_id(voice_name: str) -> str:
    """
    Get voice ID from voice name.
    
    Args:
        voice_name: Name of the voice (e.g., "george", "adam")
    
    Returns:
        Voice ID string
    """
    return VOICES.get(voice_name.lower(), VOICES["george"])


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python create_audio.py <text_file> [output_file] [voice_name]")
        print("Example: python create_audio.py analysis.txt analysis.mp3 george")
        print(f"\nAvailable voices: {', '.join(VOICES.keys())}")
        sys.exit(1)
    
    text_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "analysis.mp3"
    voice_name = sys.argv[3] if len(sys.argv) > 3 else "george"
    
    try:
        voice_id = get_voice_id(voice_name)
        analyze_text_to_speech_from_file(text_file, output_file)
        
        print("\n" + "="*60)
        print("SUCCESS!")
        print(f"Audio file created: {output_file}")
        print(f"Voice used: {voice_name}")
        print("="*60)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

