from pydantic import BaseModel
from typing import Literal
from enum import Enum

class VideoPlatform(str, Enum):
    REEL = "reel"       # 9:16 (TikTok, Shorts, Reels)
    YOUTUBE = "youtube" # 16:9 (Standard Video)

class VideoRequest(BaseModel):
    surah: int
    ayah_start: int
    ayah_end: int
    reciter_id: str = "ar.alafasy"
    translation_id: str = "en.sahih"
    background_url: str = "https://www.pexels.com/download/video/34464845/"
    platform: VideoPlatform = VideoPlatform.REEL
    resolution: Literal[360, 480, 720, 1080] = 720
