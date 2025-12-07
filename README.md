# Quran Reels Backend

This is the FastAPI backend for the Quran Reels application. It handles video generation by combining Quran recitation audio, translations, and background videos.

## Features
- **Video Generation**: Creates 9:16 (Reel) or 16:9 (YouTube) videos.
- **Audio Processing**: Fetches audio from `https://api.quran.com`.
- **Subtitle Overlay**: Adds synchronized Arabic and English subtitles.
- **Backgrounds**: Uses Pexels API or static video links for backgrounds.

## Prerequisites
- Python 3.9+
- [FFmpeg](https://ffmpeg.org/) installed and added to system PATH.

## Installation

1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Start the development server:
```bash
python run_api.py
```
The API will be available at `http://localhost:8000`.

## API Endpoints

### `POST /api/v1/generate-video`
Generates a video based on the provided parameters.

**Request Body:**
```json
{
  "surah": 108,
  "ayah_start": 1,
  "ayah_end": 1,
  "reciter_id": "ar.alafasy",
  "platform": "reel"
}
```

- `platform`: "reel" (9:16) or "youtube" (16:9).

## Project Structure
- `app/`: Main application code.
    - `api/`: API route definitions.
    - `services/`: Core logic (video generation).
    - `models.py`: Pydantic data models.
- `fonts/`: Font files for video text.
- `tests/`: Unit and integration tests.
