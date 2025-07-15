from faster_whisper import WhisperModel
import os

# Load model
model = WhisperModel("base", compute_type="int8")  # Smallest + fast

# Folder containing chunks
# chunk_folder = "audio_chunks"

# # Sort the chunks numerically
# chunk_files = sorted(os.listdir(chunk_folder), key=lambda x: int(x.split('_')[1].split('.')[0]))

# # Transcribe each chunk
# for chunk_file in chunk_files:
#     chunk_path = os.path.join(chunk_folder, chunk_file)
#     print(f"\n🔊 Transcribing: {chunk_file}")
    
#     segments, _ = model.transcribe(chunk_path)
#     full_text = " ".join([seg.text for seg in segments])

#     print(full_text)
#     # for segment in segments:
#     #     print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")


def audio_to_transcribe(path_to_audio:str):
    segments, _ = model.transcribe(path_to_audio)
    full_text = " ".join([seg.text for seg in segments])
    return full_text
