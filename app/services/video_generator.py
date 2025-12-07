import os
import gc
import subprocess
import requests
from moviepy import (
    AudioFileClip, VideoFileClip, concatenate_audioclips
)
from app.models import VideoRequest, VideoPlatform
from app.core.config import settings
from app.core.logging import setup_logging
from app.utils.arabic import formatArabicSentences
from app.utils.file_ops import download_file, cleanup_temp_dir
from app.services.text_renderer import create_text_image

logger = setup_logging()

def generate_video(request: VideoRequest) -> str:
    logger.info("=" * 80)
    logger.info(f"Starting Quran Video Generation ({request.platform.value}) via Zero-Copy FFmpeg")
    logger.info("=" * 80)
    
    # Determine Output Dimensions
    if request.platform == VideoPlatform.REEL:
        target_width = settings.REEL_WIDTH
        target_height = settings.REEL_HEIGHT
    else: # YOUTUBE
        target_width = settings.YOUTUBE_WIDTH
        target_height = settings.YOUTUBE_HEIGHT

    cleanup_temp_dir(settings.TEMP_DIR)
    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

    output_filename = os.path.join(settings.OUTPUT_DIR, f"quran_{request.platform.value}_{request.surah}_{request.ayah_start}-{request.ayah_end}.mp4")
    
    # PHASE 1: Data Fetching (Keep existing logic)
    # ... (Fetching Quran Data - simplified for brevity, assume valid)
    quran_api_url = f"http://api.alquran.cloud/v1/surah/{request.surah}/editions/{request.reciter_id},{request.translation_id}"
    response = requests.get(quran_api_url, timeout=10)
    quran_data = response.json()
    editions = quran_data['data'] if isinstance(quran_data['data'], list) else quran_data['data']['editions']
    
    arabic_data = next(e for e in editions if e['edition']['identifier'] == request.reciter_id)
    english_data = next(e for e in editions if e['edition']['identifier'] == request.translation_id)
    
    ayah_clips_info = []
    
    for i in range(len(arabic_data['ayahs'])):
        num = arabic_data['ayahs'][i]['numberInSurah']
        if request.ayah_start <= num <= request.ayah_end:
            # Audio
            audio_url = arabic_data['ayahs'][i].get('audio')
            if not audio_url:
                audio_url = f"https://everyayah.com/data/{request.reciter_id}/{request.surah:03d}{num:03d}.mp3"
            
            audio_path = os.path.join(settings.TEMP_DIR, f"audio_{num}.mp3")
            download_file(audio_url, audio_path)
            
            # Duration Check (using ffprobe or moviepy lightweight)
            try:
                clip = AudioFileClip(audio_path)
                duration = clip.duration
                clip.close()
            except:
                duration = 5.0 # Fallback
            
            # Generate Text Image
            image_path = os.path.join(settings.TEMP_DIR, f"text_{num}.png")
            create_text_image(
                formatArabicSentences(arabic_data['ayahs'][i]['text']),
                english_data['ayahs'][i]['text'],
                image_path,
                target_width,
                target_height
            )

            ayah_clips_info.append({
                'audio': audio_path,
                'image': image_path,
                'duration': duration
            })

    # PHASE 2: Background
    bg_path = os.path.join(settings.TEMP_DIR, "bg.mp4")
    if not download_file(request.background_url, bg_path):
        bg_path = 'videos/default_background.mp4'

    # PHASE 3: Concatenate Audio (MoviePy is fine here, lightweight)
    final_audio_path = os.path.join(settings.TEMP_DIR, "final_audio.mp3")
    audio_clips = [AudioFileClip(x['audio']) for x in ayah_clips_info]
    final_audio = concatenate_audioclips(audio_clips)
    final_audio.write_audiofile(final_audio_path, logger=None)
    final_audio.close()
    for c in audio_clips: c.close()
    
    total_duration = sum(x['duration'] for x in ayah_clips_info)

    # PHASE 4: FFmpeg Composition (The Magic)
    # Inputs: 0:BG, 1:Audio, 2..N:Images
    # Filter: crop bg, loop bg, overlay images at timestamps
    
    inputs = ["-stream_loop", "-1", "-i", bg_path, "-i", final_audio_path]
    filter_complex = []
    
    # Crop/Scale Background
    # scale=-2:h (maintain aspect), crop=w:h
    filter_complex.append(f"[0:v]scale=-2:{target_height},crop={target_width}:{target_height},setsar=1[bg]")
    
    last_stream = "[bg]"
    current_time = 0.0
    
    for idx, clip in enumerate(ayah_clips_info):
        inputs.extend(["-i", clip['image']])
        image_input_idx = idx + 2 # 0 is bg, 1 is audio
        
        start_t = current_time
        end_t = current_time + clip['duration']
        
        # Overlay
        # enable='between(t,START,END)'
        next_stream = f"[v{idx}]"
        filter_complex.append(f"{last_stream}[{image_input_idx}:v]overlay=0:0:enable='between(t,{start_t:.2f},{end_t:.2f})'{next_stream}")
        
        last_stream = next_stream
        current_time += clip['duration']

    # Map output
    # Limit duration to audio duration
    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", ";".join(filter_complex),
        "-map", last_stream, 
        "-map", "1:a", 
        "-t", str(total_duration),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p", # Essential for compatibility
        output_filename
    ]
    
    logger.info(f"Running FFmpeg: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    
    # Cleanup
    cleanup_temp_dir(settings.TEMP_DIR)
    
    return output_filename

