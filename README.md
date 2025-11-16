# YouTube Media Fetcher

YouTube Media Fetcher is a refactored, high-performance web application designed to download YouTube videos, audio, and playlists reliably. It features a clean, modern frontend and a powerful, modular Flask backend driven by a centralized `yt-dlp` download manager.

![App Screenshot](https://i.imgur.com/your-new-screenshot.png) <!-- TODO: Update screenshot -->

## Core Features

- **Modular Architecture**: A clean project structure with separated concerns for web routes, download logic, and configuration.
- **Centralized Download Manager**: All `yt-dlp` logic is handled by a single, robust `DownloadManager` class, making the system easy to maintain and extend.
- **Server-Side Downloads**: Files are downloaded to the server first and then served to the user, a reliable architecture perfect for containerized deployments.
- **Playlist & Video Support**: Download entire playlists or single videos with the same interface.
- **Expanded Format Selection**:
    - **Video**: MP4
    - **Audio**: MP3, WAV, M4A
- **Quality Control**: Selectable quality tiers for both audio and video.
- **Cookie-Free Operation**: Downloads public content reliably without the need for `cookies.txt` by simulating a mobile client.
- **Dynamic UI**: The frontend, built with TailwindCSS and vanilla JavaScript, intelligently handles user input, fetches media info, and displays download links.
- **Dockerized for Production**: The entire application is containerized, ensuring a consistent and stable environment for both local development and deployment on platforms like Render.

## Project Structure

```
├── Dockerfile
├── README.md
├── requirements.txt
└── src
    ├── __init__.py
    ├── downloader
    │   ├── __init__.py
    │   └── manager.py  # Central DownloadManager class
    └── web
        ├── __init__.py
        ├── app.py        # Flask routes and application logic
        ├── static
        │   └── app.js    # Frontend JavaScript
        └── templates
            └── index.html # Main HTML file
```

## How to Run Locally

### Prerequisites

-   Python 3.11+ & `pip`
-   **Docker**: The recommended method for running the application.
-   **ffmpeg** (if not using Docker): Required for audio/video processing.

### Option 1: Running with Docker (Recommended)

1.  **Build the Docker image:**
    ```bash
    docker build -t youtube-media-fetcher .
    ```
2.  **Run the Docker container:**
    ```bash
    docker run -p 8080:8080 youtube-media-fetcher
    ```
3.  Open your browser to `http://127.0.0.1:8080`.

### Option 2: Running Directly with Python

1.  **Clone the repository and install dependencies:**
    ```bash
    git clone <your-repo-url>
    cd youtube-media-fetcher
    pip install -r requirements.txt
    ```
2.  **Run the Flask application from the project root:**
    ```bash
    python -m src.web.app
    ```
3.  Open your browser to `http://127.0.0.1:8080`.

## Deployment on Render

This application is optimized for deployment on [Render](https://render.com/) via Docker.

1.  **Fork this repository** to your GitHub account.
2.  On the **Render Dashboard**, click **"New +"** -> **"Web Service"**.
3.  Connect your GitHub account and select your forked repository.
4.  Render will prompt you to choose a runtime. Select **Docker**.
5.  Render will automatically detect the `Dockerfile` and build/deploy your service. All settings, including the start command, are handled by the `Dockerfile`.
6.  Give your service a name and click **"Create Web Service"**.

## How It Works

1.  The user enters a YouTube URL or search query into the frontend.
2.  The frontend sends a request to the Flask backend (`/info` or `/search`).
3.  The backend's `DownloadManager` uses `yt-dlp` to fetch the media's metadata without downloading the full content.
4.  The frontend displays the metadata (thumbnail, title).
5.  The user clicks the "Download" button.
6.  The frontend sends a request to the `/download` endpoint with the URL, format, and quality.
7.  The `DownloadManager` downloads the media to a temporary directory (`/tmp/downloads`) on the server.
8.  The backend returns a JSON response containing a unique URL to the downloaded file (e.g., `/downloads/my-video.mp4`).
9.  The frontend creates and displays a download link pointing to this URL, which the user can click to save the file.
