# YouTube Media Fetcher

YouTube Media Fetcher is a modern, production-ready web application that allows users to download YouTube videos as MP3 (audio) or MP4 (video) files with selectable quality options. It features a sleek, responsive frontend built with TailwindCSS and a robust Flask backend powered by `yt-dlp`.

![App Screenshot](https://i.imgur.com/your-screenshot.png) <!-- Placeholder -->

## Features

- **Single-Page Application**: A clean, beautiful, and intuitive user interface.
- **Multiple Formats**: Download media as MP4 (video) or MP3 (audio).
- **Quality Selection**:
    - **MP4**: Best Available, 1080p, 720p, 360p.
    - **MP3**: High (320kbps), Medium (192kbps), Low (128kbps).
- **Video Preview**: Shows video thumbnail and title automatically after pasting a URL.
- **Responsive Design**: Looks great on both desktop and mobile devices.
- **Dark/Light Theme**: A theme toggle for user preference.
- **User-Friendly Notifications**: Animated, elegant alerts for errors, progress, and success.
- **Reliable Backend**: Uses the powerful `yt-dlp` library for downloading and `ffmpeg` for conversion.
- **Automatic Cleanup**: Temporary files are deleted immediately after being sent to the user.
- **Ready for Deployment**: Includes configuration for one-click deployment on Render.com.

## How to Run Locally

Follow these steps to get the application running on your local machine.

### Prerequisites

- Python 3.11+
- `pip` (Python package installer)
- `ffmpeg`: This must be installed and available in your system's PATH.
    - **macOS (with Homebrew)**: `brew install ffmpeg`
    - **Ubuntu/Debian**: `sudo apt-get update && sudo apt-get install ffmpeg`
    - **Windows**: Download from the [official website](https://ffmpeg.org/download.html) and add the `bin` directory to your PATH.

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/youtube-media-fetcher.git
    cd youtube-media-fetcher
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Flask application:**
    ```bash
    flask run
    ```
    Alternatively, for development mode:
    ```bash
    python app.py
    ```

5.  **Open your browser** and navigate to `http://127.0.0.1:5000` (or the address shown in your terminal).

## How to Deploy on Render

This application is configured for easy deployment on [Render](https://render.com/).

### One-Click Deployment

You can deploy your own instance of this app by clicking the button below:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/your-username/youtube-media-fetcher)

*(You will need to replace the repository URL in the button link with your own once you've forked/cloned it.)*

### Manual Deployment Steps

1.  **Fork this repository** to your own GitHub account.
2.  **Go to the Render Dashboard** and click **"New +"** -> **"Web Service"**.
3.  **Connect your GitHub account** and select your forked repository.
4.  **Configure the service:**
    - **Name**: `youtube-media-fetcher` (or your preferred name).
    - **Region**: Choose a region close to you.
    - **Branch**: `main` (or your default branch).
    - **Build Command**: `pip install -r requirements.txt && apt-get update && apt-get install -y ffmpeg`
    - **Start Command**: `gunicorn app:app --timeout 120`
    - **Instance Type**: `Free` is sufficient for basic use.

5.  **Click "Create Web Service"**. Render will automatically build and deploy your application. The `render.yaml` file in this repository ensures these settings are applied by default.

## Maintenance & Customization

### Updating `yt-dlp`

YouTube frequently changes its backend, which can break download functionality. `yt-dlp` is updated regularly to fix these issues. To keep the app working, you should update it periodically.

-   **Locally**:
    ```bash
    pip install --upgrade yt-dlp
    ```
-   **On Render**: You can redeploy your application from the Render dashboard (select "Manual Deploy" -> "Deploy latest commit"). This will reinstall all packages, including the latest version of `yt-dlp` available at that time.

### Modifying Quality Options

You can easily change the available quality options.

1.  **Backend (`app.py`)**:
    -   Modify the dictionaries inside the `/download` route to change the `yt-dlp` format codes or FFmpeg quality settings.
    ```python
    # Example for MP3 quality
    'preferredquality': {
        'Low': '128', # Change bitrate here
        'Medium': '192',
        'High': '320'
    }
    ```

2.  **Frontend (`static/app.js`)**:
    -   Update the `qualityOptions` object to match the options you want to display to the user.
    ```javascript
    const qualityOptions = {
        mp4: ['Best Available', '1080p', '720p', '480p', '360p'], // Added 480p
        mp3: ['High', 'Medium', 'Low']
    };
    ```

### Customizing the Design

The frontend is built with **TailwindCSS** and is easy to customize.

-   **Colors & Theme**: Edit the CSS custom properties (`:root`) in the `<style>` tag of `templates/index.html`.
-   **Layout & Components**: Modify the HTML structure and TailwindCSS classes in `templates/index.html`.
-   **Behavior**: All frontend logic is located in `static/app.js`. You can change animations, alerts, and interaction logic here.