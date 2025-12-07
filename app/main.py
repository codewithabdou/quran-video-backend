from fastapi import FastAPI
from app.api.v1.endpoints import router as api_router
from app.core.config import settings

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development convenience, allowing all. In production, be specific.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
@app.head("/")
async def root():
    return {"message": "Welcome to Quran Video Generator API. Use POST /api/v1/generate-video to create videos."}
