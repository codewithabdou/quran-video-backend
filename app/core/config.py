import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "Quran Video Generator API"
    API_V1_STR: str = "/api/v1"
    
    # Platform Defaults (Optimized for Free Tier)
    REEL_WIDTH: int = 720
    REEL_HEIGHT: int = 1280
    
    YOUTUBE_WIDTH: int = 1280
    YOUTUBE_HEIGHT: int = 720
    
    # Video Settings
    FPS: int = 24
    VIDEO_CODEC: str = "libx264"
    AUDIO_CODEC: str = "aac"
    VIDEO_BITRATE: str = "8000k"
    AUDIO_BITRATE: str = "192k"
    
    # Text Settings
    ARABIC_FONT_COLOR: str = "#FFFFFF"
    ENGLISH_FONT_COLOR: str = "#CCCCCC"
    FONT_SIZE: int = 70
    
    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    FONTS_DIR: str = os.path.join(BASE_DIR, "fonts")
    TEMP_DIR: str = os.path.join(BASE_DIR, "temp_assets")
    OUTPUT_DIR: str = os.path.join(BASE_DIR, "outputs")
    LOGS_DIR: str = os.path.join(BASE_DIR, "logs")
    
    ARABIC_FONT: str = os.path.join(FONTS_DIR, "Amiri-Regular.ttf")
    ENGLISH_FONT: str = os.path.join(FONTS_DIR, "arial.ttf")
    
    class Config:
        env_file = ".env"

settings = Settings()
