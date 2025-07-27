# import os
# import asyncio
# import edge_tts

# OUT_DIR_QUESTIONS = "OUT_DIR_Questions"
# os.makedirs(OUT_DIR_QUESTIONS, exist_ok=True)

#   :
#     """
#     Convert text to speech using edge-tts and save it to a file.
    
#     Args:
#         text (str): The text to synthesize.
#         filename (str): Name of the audio file (without extension).
#         voice (str): Edge TTS voice ID. Default is English male.
#     """
#     output_path = os.path.join(OUT_DIR_QUESTIONS, f"{filename}.mp3")

#     communicate = edge_tts.Communicate(text=text, voice=voice)
#     await communicate.save(output_path)

#     print(f"🔊 Saved: {output_path}")
#     return output_path

# # Example usage
# if __name__ == "__main__":
#     sample_text = "Can you describe the specific challenges you encountered when deploying your app with Docker?"
#     asyncio.run(text_to_speech(sample_text, "docker_question"))

# import os
# import asyncio
# from gtts import gTTS

# OUT_DIR_QUESTIONS = "OUT_DIR_Questions"
# os.makedirs(OUT_DIR_QUESTIONS, exist_ok=True)

# async def text_to_speech(text: str, filename: str, lang="en", retries=3):
#     """
#     Convert text to speech using gTTS and save it to a file, with retries.

#     Args:
#         text (str): The text to synthesize.
#         filename (str): Name of the audio file (without extension).
#         lang (str): Language code for TTS (default: "en").
#         retries (int): Number of retry attempts on failure.
#     """
#     output_path = os.path.join(OUT_DIR_QUESTIONS, f"{filename}.mp3")

#     for attempt in range(1, retries + 1):
#         try:
#             # Run the blocking gTTS code in a thread-safe way
#             await asyncio.to_thread(lambda: gTTS(text=text, lang=lang).save(output_path))
#             print(f"🔊 Saved: {output_path}")
#             return output_path
#         except Exception as e:
#             print(f"❌ gTTS failed on attempt {attempt} for {filename}: {e}")
#             await asyncio.sleep(2 ** attempt)

#     raise RuntimeError(f"gTTS failed after {retries} retries for: {filename}")

import os
import asyncio
from gtts import gTTS

OUT_DIR_QUESTIONS = "OUT_DIR_Questions"
os.makedirs(OUT_DIR_QUESTIONS, exist_ok=True)

# Only use language codes gTTS supports
def normalize_lang_for_gtts(voice: str) -> str:
    voice = voice.lower()
    if voice.startswith("en"):
        return "en"
    elif voice.startswith("hi"):
        return "hi"
    elif voice.startswith("fr"):
        return "fr"
    elif voice.startswith("de"):
        return "de"
    # Add more mappings as needed
    return "en"  # fallback

async def text_to_speech(text: str, filename: str, voice: str = "en", retries: int = 3):
    """
    Convert text to speech using gTTS and save to an MP3 file with retries.

    Args:
        text (str): Text to convert.
        filename (str): File name without extension.
        voice (str): Voice or language ID (normalized internally).
        retries (int): Retry attempts on failure.
    """
    output_path = os.path.join(OUT_DIR_QUESTIONS, f"{filename}.mp3")
    lang = normalize_lang_for_gtts(voice)

    for attempt in range(1, retries + 1):
        try:
            await asyncio.to_thread(lambda: gTTS(text=text, lang=lang).save(output_path))
            print(f"🔊 Saved: {output_path}")
            return output_path
        except Exception as e:
            print(f"❌ gTTS failed on attempt {attempt} for {filename}: {e}")
            await asyncio.sleep(2 ** attempt)

    raise RuntimeError(f"gTTS failed after {retries} retries for: {filename}")

# if __name__ == "__main__":
#     sample_text = "Can you describe the specific challenges you encountered when deploying your app with Docker?"
#     asyncio.run(text_to_speech(sample_text, "docker_question", voice="en-US-AndrewMultilingualNeural"))
