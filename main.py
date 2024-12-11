import os
import asyncio
import aiohttp
from tqdm import tqdm
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from hashlib import sha256

from dotenv import load_dotenv
load_dotenv()

FLIC_TOKEN = "flic_23fa225b1cdfeef1b05f01e48bb3f24f190bbaba37cfbf61b897d4e5b5097ce6"
BASE_API_URL = "https://api.socialverseapp.com"

HEADERS = {
    "Flic-Token": FLIC_TOKEN,
    "Content-Type": "application/json"
}

VIDEOS_DIR = "./videos"


async def fetch_upload_url(session):
    print("Fetching upload URL...")
    async with session.get(f"{BASE_API_URL}/posts/generate-upload-url", headers=HEADERS) as response:
        print(f"Response status: {response.status}")
        if response.status != 200:
            text = await response.text()
            print(f"Error response: {text}")
            raise Exception("Failed to get upload URL")
        return await response.json()

    response_data = await response.json()
    print(f"Upload URL response: {response_data}")


async def upload_video(session, file_path, upload_url):
    print(f"Uploading video to: {upload_url}")
    try:
        with open(file_path, "rb") as file:
            async with session.put(upload_url, data=file) as response:
                print(f"Upload response status: {response.status}")
                if response.status != 200:
                    text = await response.text()
                    print(f"Upload error: {text}")
                    raise Exception(f"Upload failed for {file_path}")
                print(f"Uploaded {file_path}")
    except Exception as e:
        print(f"Error during upload: {e}")


async def create_post(session, title, video_hash, category_id):
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
            # Accept 200 or 201 as valid success statuses
            if response.status not in [200, 201]:
                raise Exception(f"Failed to create post with status {response.status}: {text}")
            return await response.json()
    except Exception as e:
        print(f"Error during post creation: {e}")
        raise


def calculate_hash(file_path):
    hash_sha256 = sha256()
    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


async def process_video(file_path):
    async with aiohttp.ClientSession() as session:
        print(f"Processing file: {file_path}")
        try:
            upload_data = await fetch_upload_url(session)
            print(f"Fetched upload data: {upload_data}")
            await upload_video(session, file_path, upload_data["url"])
            print("Video uploaded successfully.")
            video_hash = upload_data["hash"]
            await create_post(session, os.path.basename(file_path), video_hash, category_id=1)
            print("Post created successfully.")
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        except Exception as e:
            print(f"Error processing video: {e}")


class VideoHandler(FileSystemEventHandler):
    def __init__(self, loop):
        self.loop = loop

    def on_created(self, event):
        print(f"Event detected: {event}")
        if event.is_directory or not event.src_path.endswith(".mp4"):
            return
        print(f"New video detected: {event.src_path}")
        asyncio.run_coroutine_threadsafe(process_video(event.src_path), self.loop)


def monitor_directory(loop):
    event_handler = VideoHandler(loop)
    observer = Observer()
    observer.schedule(event_handler, VIDEOS_DIR, recursive=False)
    observer.start()
    print(f"Monitoring directory: {VIDEOS_DIR}")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    if not os.path.exists(VIDEOS_DIR):
        os.makedirs(VIDEOS_DIR)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    monitor_directory(loop)








