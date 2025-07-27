import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)

async def upload_audio_async(file_path):
    loop = asyncio.get_event_loop()
    try:
        # Wrap the sync upload function to run in executor (non-blocking)
        upload_result = await loop.run_in_executor(
            None,
            lambda: cloudinary.uploader.upload(
                file_path,
                resource_type="auto"
                # notification_url="https://www.example.com/cloudinary_webhook"
            )
        )
        print(f"Async upload completed for: {file_path}. Public ID: {upload_result['public_id']}")
        return upload_result['public_id']
    except Exception as e:
        print(f"Error uploading audio asynchronously: {e}")
        return None
