import os
from pydub import AudioSegment
# from yt_dlp import YoutubeDL

# -----------------------
# Configuration
# -----------------------
YOUTUBE_URL = "https://www.youtube.com/watch?v=VIDEO_ID"  # Replace this
OUTPUT_DIR = "audio_chunks"
CHUNK_LENGTH_MS = 30 * 1000  # 30 seconds

# -----------------------
# Step 1: Download audio
# -----------------------
# def download_audio(youtube_url: str, output_path="audio.mp3") -> str:
#     ydl_opts = {
#         'format': 'bestaudio/best',
#         'outtmpl': 'temp_audio.%(ext)s',
#         'postprocessors': [{
#             'key': 'FFmpegExtractAudio',
#             'preferredcodec': 'mp3',
#             'preferredquality': '192',
#         }],
#         'quiet': True
#     }

#     with YoutubeDL(ydl_opts) as ydl:
#         ydl.download([youtube_url])
    
#     if os.path.exists("temp_audio.mp3"):
#         os.rename("temp_audio.mp3", output_path)
#     return output_path

# -----------------------
# Step 2: Split audio
# -----------------------
from pydub import AudioSegment
import os

def split_audio(audio_path: str, output_dir: str, chunk_length_ms: int):
    os.makedirs(output_dir, exist_ok=True)

    audio = AudioSegment.from_mp3(audio_path)
    total_length = len(audio)
    chunk_count = 0

    for start in range(0, total_length, chunk_length_ms):
        end = min(start + chunk_length_ms, total_length)
        chunk = audio[start:end]

        output_path = os.path.join(output_dir, f"chunk_{chunk_count}.mp3")
        chunk.export(output_path, format="mp3")
        chunk_count += 1

        yield output_path  # 👈 stream path of each chunk

    print(f"✅ Audio split into {chunk_count} chunks in '{output_dir}' folder.")
# -----------------------
# Run the pipeline
# -----------------------
# if __name__ == "__main__":
#     print("📥 Downloading audio...")
#     # audio_path = download_audio(YOUTUBE_URL)
#     audio_path = "./Docker in 100 Seconds.mp3"
#     print("🔪 Splitting into chunks...")    
#     split_audio(audio_path, OUTPUT_DIR,CHUNK_LENGTH_MS)

#     print("✅ Done.")
