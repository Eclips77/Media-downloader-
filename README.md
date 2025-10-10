# YouTube Media Fetcher

YouTube Media Fetcher is a modern, production-ready web application that allows users to download YouTube videos as MP3 (audio) or MP4 (video) files with selectable quality options. It features a sleek, responsive frontend built with TailwindCSS and a robust, containerized Flask backend powered by `yt-dlp`.

![App Screenshot](https://i.imgur.com/your-screenshot.png) <!-- Placeholder for a future screenshot -->

## Features

- **Single-Page Application**: A clean, beautiful, and intuitive user interface.
- **Multiple Formats**: Download media as MP4 (video) or MP3 (audio).
- **Quality Selection**:
    - **MP4**: Best Available, 1080p, 720p, 360p.
    - **MP3**: High (320kbps), Medium (192kbps), Low (128kbps).
- **Cookie Support**: Upload your browser's `cookies.txt` file to download age-restricted, private, or members-only videos.
- **Video Preview**: Shows video thumbnail and title automatically after pasting a URL.
- **Responsive Design**: Looks great on both desktop and mobile devices.
- **Dark/Light Theme**: A theme toggle for user preference.
- **User-Friendly Notifications**: Animated, elegant alerts for errors, progress, and success.
- **Reliable Backend**: Uses the powerful `yt-dlp` library for downloading and `ffmpeg` for conversion.
- **Automatic Cleanup**: Temporary files are deleted immediately after being sent to the user.
- **Containerized Deployment**: Uses Docker for a stable, reliable, and easy-to-deploy application on services like Render.

## Using Cookies for Restricted Videos

Many YouTube videos are now protected (e.g., age-restricted, private, members-only) and require you to be logged in to view them. To download these videos, you must provide the application with your browser's YouTube cookies.

### How to Get Your `cookies.txt` File

1.  **Install a Browser Extension**: Use an extension that can export cookies in the standard `Netscape` format (usually a `cookies.txt` file). A recommended extension is:
    *   **Get cookies.txt** ([Chrome](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfdhebiahabn) / [Firefox](https://addons.mozilla.org/en-US/firefox/addon/get-cookiestxt/))

2.  **Export the Cookies**:
    *   Go to `https://www.youtube.com` and make sure you are logged into your account.
    *   Click the extension's icon in your browser toolbar.
    *   Click the **"Export"** or **"Export as .txt"** button.
    *   Save the `cookies.txt` file to your computer.

3.  **Upload to the App**:
    *   In the YouTube Media Fetcher app, click the **"Choose File"** button under "YouTube Cookies (Optional)".
    *   Select the `cookies.txt` file you just downloaded.
    *   Now, when you click "Download", your cookies will be used to authenticate with YouTube.

## How to Run Locally

### Prerequisites

-   Python 3.11+ & `pip`
-   **Docker**: The easiest way to run the app locally is with Docker, as it handles all dependencies.
-   **ffmpeg** (if not using Docker): This must be installed on your system.

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
2.  **Run the Flask application:**
    ```bash
    python app.py
    ```
3.  Open your browser to `http://127.0.0.1:8080`.

## How to Deploy on Render

This application is configured for easy, one-click deployment on [Render](https://render.com/) using Docker.

1.  **Fork this repository** to your own GitHub account.
2.  Go to the **Render Dashboard**, click **"New +"** -> **"Web Service"**.
3.  Connect your GitHub account and select your forked repository.
4.  Render will automatically detect the `render.yaml` file and configure the service to use **Docker**. All settings, including the start command, are handled by the `Dockerfile`.
5.  Give your service a name and click **"Create Web Service"**. Render will build the Docker image and deploy your application.

## Maintenance & Customization

### Updating `yt-dlp`

To get the latest version of `yt-dlp` with fixes for YouTube's changes:
-   **Locally**: Re-build your Docker image (`docker build ...`) or run `pip install --upgrade yt-dlp`.
-   **On Render**: Go to your service's dashboard and trigger a new deploy. This will pull the latest version of `yt-dlp` as defined in `requirements.txt`.

### Modifying Quality Options

1.  **Backend (`app.py`)**: Modify the quality dictionaries in the `/download` route.
2.  **Frontend (`static/app.js`)**: Update the `qualityOptions` object to match the user-facing text.