import asyncio
from faster_whisper import WhisperModel
from langchain_core.runnables import RunnableLambda
import wave
import os
import tempfile
import subprocess

# Load Whisper model (base/int8 for CPU)
model = WhisperModel("base", compute_type="int8", cpu_threads=4)

# 🔧 Convert mp3 or other formats to wav using ffmpeg
def convert_to_wav(input_path, output_path):
    subprocess.run(["ffmpeg", "-y", "-i", input_path, "-ar", "16000", "-ac", "1", output_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# 🔁 Async audio chunk generator (50% overlap)
async def audio_chunk_generator(wav_path, chunk_duration_sec=3.0, overlap_sec=1.5):
    with wave.open(wav_path, 'rb') as wf:
        sample_rate = wf.getframerate()
        sample_width = wf.getsampwidth()
        channels = wf.getnchannels()

        chunk_size = int(chunk_duration_sec * sample_rate)
        overlap_size = int(overlap_sec * sample_rate)
        hop_size = chunk_size - overlap_size

        pos = 0
        total_frames = wf.getnframes()

        while pos < total_frames:
            wf.setpos(pos)
            frames = wf.readframes(chunk_size)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as chunk_file:
                with wave.open(chunk_file.name, 'wb') as out_wf:
                    out_wf.setnchannels(channels)
                    out_wf.setsampwidth(sample_width)
                    out_wf.setframerate(sample_rate)
                    out_wf.writeframes(frames)
                yield chunk_file.name, pos / sample_rate  # timestamp
            await asyncio.sleep(chunk_duration_sec)  # simulate real-time
            pos += hop_size

# 🔠 Async transcription
async def transcribe_chunk(chunk_path):
    segments, _ = model.transcribe(chunk_path, beam_size=5)
    os.unlink(chunk_path)  # clean up
    return " ".join([seg.text for seg in segments]).strip()

# 🧠 LangChain runnable
whisper_runnable = RunnableLambda(transcribe_chunk)

# 🚀 Main pipeline
async def run_pipeline(input_audio_path):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
        convert_to_wav(input_audio_path, temp_wav.name)
        async for chunk_path, timestamp in audio_chunk_generator(temp_wav.name):
            print(f"\n🎧 Chunk at {timestamp:.2f}s")
            transcript = await whisper_runnable.ainvoke(chunk_path)
            print("📝 Transcript:", transcript)
        os.unlink(temp_wav.name)

# 🧪 Entry
if __name__ == "__main__":
    asyncio.run(run_pipeline("./Docker in 100 Seconds.mp3"))
