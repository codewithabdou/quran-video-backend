# Quran Reels Backend

This is the FastAPI backend for the Quran Reels application. It handles video generation by combining Quran recitation audio, translations, and background videos.

## Features
- **Video Generation**: Creates 9:16 (Reel) or 16:9 (YouTube) videos.
- **Audio Processing**: Fetches audio from `https://api.quran.com`.
- **Subtitle Overlay**: Adds synchronized Arabic and English subtitles.
- **Backgrounds**: Uses Pexels API or static video links for backgrounds.

## Prerequisites
- **Python 3.9+**
- **FFmpeg**: Required for video processing. Must be added to system PATH.
- **ImageMagick**: Required for text rendering.
  - **Windows**: [Download Installer](https://imagemagick.org/script/download.php#windows). **IMPORTANT**: Check "Install legacy utilities (e.g. convert)" during installation.
  - **Linux**: `sudo apt-get install imagemagick`
  - **Mac**: `brew install imagemagick`

## Installation

1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```

2.  Create a virtual environment (Recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Start the development server:
```bash
python run_api.py
```
- API Base URL: `http://localhost:8000`
- **Interactive Docs (Swagger UI)**: `http://localhost:8000/docs`

## API Endpoints

### `POST /api/v1/generate-video`
Generates a video based on the provided parameters. The response is the `video/mp4` file content.

**Request Body:**
```json
{
  "surah": 108,
  "ayah_start": 1,
  "ayah_end": 3,
  "reciter_id": "ar.alafasy",
  "translation_id": "en.sahih",
  "background_url": "https://www.pexels.com/download/video/34464845/",
  "platform": "reel",
  "resolution": 720,
  "request_id": "optional-uuid-for-tracking"
}
```

- **platform**: `reel` (9:16) or `youtube` (16:9).
- **resolution**: `360`, `480`, `720`, or `1080`.
- **background_url**: Direct link to a video file (Pexels download links or any MP4 URL).
- **request_id**: Generate a UUID on the client side and send it here to track progress via SSE.

### `GET /api/v1/progress/{request_id}`
Server-Sent Events (SSE) endpoint for real-time progress updates.

**Usage:**
Connect an `EventSource` to this URL with the same `request_id` sent to the generation endpoint.
```javascript
const eventSource = new EventSource(`/api/v1/progress/${requestId}`);
eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data); // { status: "processing", percentage: 50, message: "Rendering..." }
};
```

## Project Structure
- `app/`: Main application code.
    - `api/`: API route definitions.
    - `services/`: Core logic (video generation).
    - `models.py`: Pydantic data models.
- `fonts/`: Font files for video text.
- `tests/`: Unit and integration tests.
