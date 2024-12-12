import os
import asyncio
import aiohttp
from tqdm import tqdm
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from hashlib import sha256

# Token for accessing the API
FLIC_TOKEN = "flic_23fa225b1cdfeef1b05f01e48bb3f24f190bbaba37cfbf61b897d4e5b5097ce6"

# Base URL for the API endpoints
BASE_API_URL = "https://api.socialverseapp.com"

# Default headers for HTTP requests
HEADERS = {
    "Flic-Token": FLIC_TOKEN,
    "Content-Type": "application/json"
}

# Directory to monitor for new video files
VIDEOS_DIR = "./videos"

# Get a pre-signed upload URL from the server
async def fetch_upload_url(session):
    """Fetches a pre-signed URL for uploading a video file."""
    print("Fetching upload URL...")
    async with session.get(f"{BASE_API_URL}/posts/generate-upload-url", headers=HEADERS) as response:
        print(f"Response status: {response.status}")
        if response.status != 200:
            # Print and raise an error if the request fails
            text = await response.text()
            print(f"Error response: {text}")
            raise Exception("Failed to get upload URL")
        return await response.json()

# Upload a video file to the server using the pre-signed URL
async def upload_video(session, file_path, upload_url):
    """Uploads the given video file to the specified pre-signed URL."""
    print(f"Uploading video to: {upload_url}")
    try:
        # Open the video file and upload it
        with open(file_path, "rb") as file:
            async with session.put(upload_url, data=file) as response:
                print(f"Upload response status: {response.status}")
                if response.status != 200:
                    # Log errors if the upload fails
                    text = await response.text()
                    print(f"Upload error: {text}")
                    raise Exception(f"Upload failed for {file_path}")
                print(f"Uploaded {file_path}")
    except Exception as e:
        print(f"Error during upload: {e}")

# Create a new post on the server for the uploaded video
async def create_post(session, title, video_hash, category_id):
    """Creates a post for the uploaded video."""
    payload = {
        "title": title,
        "hash": video_hash,
        "is_available_in_public_feed": False,
        "category_id": category_id
    }
    print(f"Creating post with payload: {payload}")
    try:
        async with session.post(f"{BASE_API_URL}/posts", json=payload, headers=HEADERS) as response:
            print(f"Create post response status: {response.status}")
            text = await response.text()
            print(f"Create post response body: {text}")
            # Treat only 200 or 201 responses as successful
            if response.status not in [200, 201]:
                raise Exception(f"Failed to create post with status {response.status}: {text}")
            return await response.json()
    except Exception as e:
        print(f"Error during post creation: {e}")
        raise

# Calculate the SHA256 hash of a file for data integrity
def calculate_hash(file_path):
    """Calculates and returns the SHA256 hash of the given file."""
    hash_sha256 = sha256()
    with open(file_path, "rb") as file:
        # Read the file in chunks to avoid memory issues with large files
        for chunk in iter(lambda: file.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

# upload and create a post
async def process_video(file_path):
    """Handles the entire workflow for processing a video file."""
    async with aiohttp.ClientSession() as session:
        print(f"Processing file: {file_path}")
        try:
            # Fetch upload URL and upload video
            upload_data = await fetch_upload_url(session)
            print(f"Fetched upload data: {upload_data}")
            await upload_video(session, file_path, upload_data["url"])
            print("Video uploaded successfully.")

            # Create a post for the uploaded video
            video_hash = upload_data["hash"]
            await create_post(session, os.path.basename(file_path), video_hash, category_id=1)
            print("Post created successfully.")

            # Delete the file after successful processing
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        except Exception as e:
            print(f"Error processing video: {e}")

# Handler for file system events
class VideoHandler(FileSystemEventHandler):
    """Handles new file creation events in the monitored directory."""
    def __init__(self, loop):
        self.loop = loop

    def on_created(self, event):
        """Triggered when a new file is created."""
        print(f"Event detected: {event}")
        if event.is_directory or not event.src_path.endswith(".mp4"):
            return
        print(f"New video detected: {event.src_path}")
        # Schedule the processing of the new video
        asyncio.run_coroutine_threadsafe(process_video(event.src_path), self.loop)

# Set up directory monitoring
def monitor_directory(loop):
    """Sets up and starts monitoring the target directory for new files."""
    event_handler = VideoHandler(loop)
    observer = Observer()
    observer.schedule(event_handler, VIDEOS_DIR, recursive=False)
    observer.start()
    print(f"Monitoring directory: {VIDEOS_DIR}")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        # Gracefully stop monitoring on keyboard interrupt
        observer.stop()
    observer.join()

# Entry point of the application
if __name__ == "__main__":
    # Ensure the target directory exists
    if not os.path.exists(VIDEOS_DIR):
        os.makedirs(VIDEOS_DIR)

    # Create and start the event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Start directory monitoring
    monitor_directory(loop)
