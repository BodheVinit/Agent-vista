from pathlib import Path
from app.core.speak import text_to_speech
from app.core.cloudinary import upload_audio_async

async def analyze_audio_url(transcript: str, fileId: str):
    # Step 1: Generate the audio file
    output_path = await text_to_speech(transcript,fileId)

    if not output_path:
        print("Text-to-speech failed. No file generated.")
        return False, "TTS failed"

    file_path = Path(output_path)

    if not file_path.exists():
        print("Generated file does not exist.")
        return False, "TTS file missing"

    # Step 2: Upload the audio file to Cloudinary
    public_id = await upload_audio_async(str(file_path))

    if not public_id:
        print("Upload to Cloudinary failed.")
        try:
            file_path.unlink()
            print(f"Deleted local file after failed upload: {file_path}")
        except Exception as e:
            print(f"Could not delete file after failed upload: {e}")
        return False, "Cloudinary upload failed"

    # Step 3: Successful upload – now delete local file
    try:
        file_path.unlink()
        print(f"File uploaded and local copy deleted: {file_path}")
    except Exception as e:
        print(f"File uploaded but failed to delete local file: {e}")

    return True, public_id
