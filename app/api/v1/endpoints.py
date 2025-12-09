from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse, StreamingResponse
from app.models import VideoRequest
from app.services.video_generator import generate_video
from app.core.logging import setup_logging
import os
import asyncio
import json
from typing import Dict

router = APIRouter()
logger = setup_logging()

# In-memory store for progress queues: request_id -> asyncio.Queue
progress_store: Dict[str, asyncio.Queue] = {}

def remove_file(path: str):
    try:
        os.remove(path)
        logger.info(f"Deleted temporary file: {path}")
    except Exception as e:
        logger.error(f"Error deleting file {path}: {e}")

@router.get("/progress/{request_id}")
async def progress_stream(request: Request, request_id: str):
    """Server-Sent Events (SSE) endpoint for progress updates."""
    
    async def event_generator():
        # Retry logic: Wait for request_id to register (handling race condition)
        for _ in range(10):
            if request_id in progress_store:
                break
            await asyncio.sleep(0.5)
        
        if request_id not in progress_store:
            yield f"data: {json.dumps({'error': 'Invalid request ID or timeout'})}\n\n"
            return

        queue = progress_store[request_id]
        
        try:
            while True:
                # Wait for new progress data
                # Use wait_for to allow checking for client disconnect (though simple yield works mostly)
                if await request.is_disconnected():
                    break
                    
                data = await queue.get()
                
                if data == "DONE":
                    yield f"data: {json.dumps({'status': 'complete', 'percentage': 100})}\n\n"
                    break
                
                if isinstance(data, dict) and "error" in data:
                     yield f"data: {json.dumps(data)}\n\n"
                     break

                # Send progress update
                yield f"data: {json.dumps(data)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            # Cleanup
            if request_id in progress_store:
                del progress_store[request_id]

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/generate-video")
async def generate_video_endpoint(request: VideoRequest, background_tasks: BackgroundTasks):
    try:
        logger.info(f"Received request: {request}")
        
        # Run Sync CPU-bound task in thread pool to avoid blocking Event Loop (crucial for SSE)
        loop = asyncio.get_running_loop() # Capture valid loop in main thread

        # Helper to push mapped progress to queue from sync thread
        def progress_callback(percentage, message):
            if request.request_id and request.request_id in progress_store:
                try:
                    queue = progress_store[request.request_id]
                    # Use the captured 'loop' from the main thread
                    loop.call_soon_threadsafe(
                        queue.put_nowait, 
                        {"status": "processing", "percentage": percentage, "message": message}
                    )
                except Exception as e:
                    logger.error(f"Error updating progress: {e}")

        # Initialize progress queue if ID provided
        if request.request_id:
            progress_store[request.request_id] = asyncio.Queue()

        video_path = await loop.run_in_executor(None, generate_video, request, progress_callback)
        
        # Signal completion
        if request.request_id and request.request_id in progress_store:
             progress_store[request.request_id].put_nowait("DONE")
        
        if not os.path.exists(video_path):
            raise HTTPException(status_code=500, detail="Video generation failed")
            
        background_tasks.add_task(remove_file, video_path)
        return FileResponse(video_path, media_type="video/mp4", filename=os.path.basename(video_path))
        
    except ValueError as e:
        if request.request_id and request.request_id in progress_store:
            progress_store[request.request_id].put_nowait({"error": str(e)})
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if request.request_id and request.request_id in progress_store:
             progress_store[request.request_id].put_nowait({"error": str(e)})
        logger.error(f"Internal server error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
