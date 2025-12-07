from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from app.models import VideoRequest
from app.services.video_generator import generate_video
from app.core.logging import setup_logging
import os

router = APIRouter()
logger = setup_logging()

def remove_file(path: str):
    try:
        os.remove(path)
        logger.info(f"Deleted temporary file: {path}")
    except Exception as e:
        logger.error(f"Error deleting file {path}: {e}")

@router.post("/generate-video")
async def generate_video_endpoint(request: VideoRequest, background_tasks: BackgroundTasks):
    try:
        logger.info(f"Received request: {request}")
        video_path = generate_video(request)
        
        if not os.path.exists(video_path):
            raise HTTPException(status_code=500, detail="Video generation failed")
            
        background_tasks.add_task(remove_file, video_path)
        return FileResponse(video_path, media_type="video/mp4", filename=os.path.basename(video_path))
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal server error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
