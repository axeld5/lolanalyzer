import anthropic
import os
from dotenv import load_dotenv
from elevenlabs import ElevenLabs
load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

message = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1000,
    messages=[
        {
            "role": "user",
            "content": "What should I search for to find the latest developments in renewable energy?"
        }
    ]
)

output = message.content[0].text
xi_client = ElevenLabs(
    base_url="https://api.elevenlabs.io",
    api_key=os.getenv("ELEVENLABS_API_KEY")
)
audio_stream = xi_client.text_to_speech.convert(
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    output_format="mp3_44100_128",
    text=output,
    model_id="eleven_multilingual_v2"
)
with open("output.mp3", "wb") as f:
    for chunk in audio_stream:
        f.write(chunk)