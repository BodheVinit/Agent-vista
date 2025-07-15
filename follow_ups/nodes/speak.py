import os
import asyncio
import edge_tts

OUT_DIR_QUESTIONS = "OUT_DIR_Questions"
os.makedirs(OUT_DIR_QUESTIONS, exist_ok=True)

async def text_to_speech(text: str, filename: str, voice="en-US-GuyNeural"):
    """
    Convert text to speech using edge-tts and save it to a file.
    
    Args:
        text (str): The text to synthesize.
        filename (str): Name of the audio file (without extension).
        voice (str): Edge TTS voice ID. Default is English male.
    """
    output_path = os.path.join(OUT_DIR_QUESTIONS, f"{filename}.mp3")

    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(output_path)

    print(f"🔊 Saved: {output_path}")
    return output_path

# Example usage
if __name__ == "__main__":
    sample_text = "Can you describe the specific challenges you encountered when deploying your app with Docker?"
    asyncio.run(text_to_speech(sample_text, "docker_question"))
