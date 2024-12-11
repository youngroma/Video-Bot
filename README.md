# Video-Bot

Video-Bot is a Python-based automation tool designed to monitor a directory for new video files, upload them to a server using a REST API, and then create a post on the Empowerverse app server. The bot supports asynchronous operations to enhance performance and reliability.

---

## Features
- Monitors a specified directory (`./videos`) for new `.mp4` files.
- Calculates SHA256 hash for video integrity.
- Fetches a pre-signed upload URL via API.
- Uploads videos using the pre-signed URL.
- Creates posts for uploaded videos with metadata.
- Automatically deletes videos after successful processing.

---

## Setup Instructions

### Prerequisites
1. Python 3.8 or higher.
2. `pip` package manager.
3. Clone this repository:
   ```bash
   git clone https://github.com/youngroma/Video-Bot.git
   cd Video-Bot
   ```
4. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Change `FLIC_TOKEN` variable:
   ```env
   FLIC_TOKEN=<your_flic_token>
   ```


---

## Usage Guidelines

### Running the Bot
1. Ensure the `./videos` directory exists in the project root:
   ```bash
   mkdir videos
   ```
2. Run the bot:
   ```bash
   python main.py
   ```
3. Place `.mp4` files into the `./videos` directory to trigger processing.

### Workflow
1. The bot detects new `.mp4` files in the directory.
2. It calculates the file's SHA256 hash.
3. Fetches a pre-signed URL from the API to upload the video.
4. Uploads the video using the pre-signed URL.
5. Creates a post using the API with metadata.
6. Deletes the video from the local directory upon successful processing.

---

## Code Overview

### Main Components

#### 1. Directory Monitoring
The bot uses the `watchdog` library to monitor the `./videos` directory for new files. It handles events asynchronously.

#### 2. Video Processing
Each detected video undergoes the following steps:
- **SHA256 Calculation:** Ensures data integrity for API requests.
- **Upload to Server:** Uses a pre-signed URL to upload the video.
- **Post Creation:** Submits metadata and file hash to the API.

#### 3. Error Handling
The bot includes robust error handling:
- Logs detailed errors for failed uploads or API calls.
- Ensures files are not deleted if an error occurs.

---


