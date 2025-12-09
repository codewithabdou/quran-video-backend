import os
import requests
from moviepy import (
    AudioFileClip, VideoFileClip, TextClip,
    CompositeVideoClip, concatenate_audioclips, vfx
)
from app.models import VideoRequest, VideoPlatform
from app.core.config import settings
from app.core.logging import setup_logging
from app.utils.arabic import formatArabicSentences
from app.utils.file_ops import download_file, cleanup_temp_dir
from app.utils.progress import ProgressLogger
import time

logger = setup_logging()

def generate_video(request: VideoRequest, progress_callback=None) -> str:
    def report_progress(p, msg):
        if progress_callback:
            progress_callback(p, msg)

    report_progress(5, "status_starting")
    
    logger.info("=" * 80)
    logger.info(f"Starting Quran Video Generation ({request.platform.value})")
    logger.info(f"Surah: {request.surah}, Ayahs: {request.ayah_start}-{request.ayah_end}")
    logger.info("=" * 80)
    
    # Determine Output Dimensions based on Resolution
    res = request.resolution
    
    if request.platform == VideoPlatform.REEL:
         # 9:16 aspect ratio
        target_width = res
        target_height = int(res * (16/9))
    else: # YOUTUBE
        # 16:9 aspect ratio
        target_height = res
        target_width = int(res * (16/9))
    
    # Ensure dimensions are divisible by 2
    target_width = target_width - (target_width % 2)
    target_height = target_height - (target_height % 2)
        
    logger.info(f"Target Resolution: {target_width}x{target_height} ({request.resolution}p)")

    cleanup_temp_dir(settings.TEMP_DIR)
    os.makedirs(settings.TEMP_DIR, exist_ok=True)

    output_filename = f"quran_{request.platform.value}_{request.surah}_{request.ayah_start}-{request.ayah_end}.mp4"
    if request.request_id:
         # Include request ID in filename to avoid collisions if concurrent (though we clean temp, output should be safe)
         output_filename = f"quran_{request.platform.value}_{request.surah}_{request.ayah_start}-{request.ayah_end}_{request.request_id}.mp4"

    output_filepath = os.path.join(settings.OUTPUT_DIR, output_filename)
    
    # PHASE 1: Data Fetching
    report_progress(10, "status_fetching")
    quran_api_url = f"http://api.alquran.cloud/v1/surah/{request.surah}/editions/{request.reciter_id},{request.translation_id}"
    
    try:
        response = requests.get(quran_api_url, timeout=10)
        response.raise_for_status()
        quran_data = response.json()
        
        if 'data' not in quran_data:
            raise ValueError("API response format is unexpected - 'data' field not found")
            
        if isinstance(quran_data['data'], list):
            editions = quran_data['data']
        elif isinstance(quran_data['data'], dict) and 'editions' in quran_data['data']:
            editions = quran_data['data']['editions']
        else:
            raise ValueError("Cannot find editions in API response")
            
    except Exception as e:
        logger.error(f"Error fetching Quran data: {str(e)}", exc_info=True)
        cleanup_temp_dir(settings.TEMP_DIR)
        raise e

    ayah_clips_info = []
    arabic_edition_data = None
    english_edition_data = None

    for edition_data in editions:
        edition_info = edition_data.get('edition', {})
        edition_id = edition_info.get('identifier', 'UNKNOWN')
        
        if edition_id == request.reciter_id:
            arabic_edition_data = edition_data
        elif edition_id == request.translation_id:
            english_edition_data = edition_data
    
    if not arabic_edition_data or not english_edition_data:
        cleanup_temp_dir(settings.TEMP_DIR)
        raise ValueError("Could not find both Arabic and English editions in API response")

    for i in range(len(arabic_edition_data['ayahs'])):
        arabic_ayah = arabic_edition_data['ayahs'][i]
        english_ayah = english_edition_data['ayahs'][i]
        ayah_number_in_surah = arabic_ayah['numberInSurah']
        
        if request.ayah_start <= ayah_number_in_surah <= request.ayah_end:
            arabic_text = arabic_ayah['text']
            english_text = english_ayah['text']
            
            if 'audio' in arabic_ayah and arabic_ayah['audio']:
                audio_url = arabic_ayah['audio']
            else:
                surah_padded = str(request.surah).zfill(3)
                ayah_padded = str(ayah_number_in_surah).zfill(3)
                audio_url = f"https://everyayah.com/data/{request.reciter_id}/{surah_padded}{ayah_padded}.mp3"
            
            audio_filename = os.path.join(settings.TEMP_DIR, f"audio_{request.surah:03d}_{ayah_number_in_surah:03d}.mp3")

            if not download_file(audio_url, audio_filename):
                cleanup_temp_dir(settings.TEMP_DIR)
                raise Exception(f"Failed to download audio for Ayah {ayah_number_in_surah}")

            ayah_clips_info.append({
                'arabic_text': arabic_text,
                'english_text': english_text,
                'audio_path': audio_filename,
                'duration': 0,
                'ayah_number': ayah_number_in_surah
            })
    
    if not ayah_clips_info:
        cleanup_temp_dir(settings.TEMP_DIR)
        raise ValueError(f"No ayahs found for Surah {request.surah} in range {request.ayah_start}-{request.ayah_end}")

    # PHASE 2: Video and Audio Processing
    report_progress(20, "status_downloading")
    background_video_filename = os.path.join(settings.TEMP_DIR, "background_video.mp4")
    if not download_file(request.background_url, background_video_filename):
        # Fallback to local default if available, otherwise fail
        default_bg = 'videos/default_background.mp4'
        if os.path.exists(default_bg):
            background_video_filename = default_bg
        else:
            cleanup_temp_dir(settings.TEMP_DIR)
            raise Exception("Failed to download background video and no local default found")

    report_progress(30, "status_processing_audio")
    audio_clips = []
    total_audio_duration = 0
    
    for info in ayah_clips_info:
        try:
            clip = AudioFileClip(info['audio_path'])
            info['duration'] = clip.duration
            audio_clips.append(clip)
            total_audio_duration += clip.duration
        except Exception as e:
            cleanup_temp_dir(settings.TEMP_DIR)
            raise Exception(f"Error loading audio clip: {str(e)}")

    concatenated_audio = concatenate_audioclips(audio_clips)

    report_progress(40, "status_processing_video")
    try:
        background_clip = VideoFileClip(background_video_filename)
        # Handle Rotation if resizing to portrait but video is landscape (and vice versa)
        is_target_portrait = target_height > target_width
        is_bg_portrait = background_clip.h > background_clip.w
        
        if is_target_portrait and not is_bg_portrait:
             background_clip = background_clip.rotated(angle=-90)
        
    except Exception as e:
        cleanup_temp_dir(settings.TEMP_DIR)
        raise Exception(f"Error loading background video: {str(e)}")

    if background_clip.w != target_width or background_clip.h != target_height:
        scale_w = target_width / background_clip.w
        scale_h = target_height / background_clip.h
        scale_factor = max(scale_w, scale_h)

        if scale_factor > 1:
            background_clip = background_clip.resized(scale_factor)

        background_clip = background_clip.cropped(
            x_center=background_clip.w / 2,
            y_center=background_clip.h / 2,
            width=target_width,
            height=target_height
        )

    # LOOPING FIX: Use seamless loop with duration instead of concatenation
    if background_clip.duration < total_audio_duration:
        # MoviePy v2.0+ uses vfx.Loop effect
        background_clip = background_clip.with_effects([vfx.Loop(duration=total_audio_duration)])
    
    background_clip = background_clip.subclipped(0, total_audio_duration)

    # PHASE 3: Subtitle Generation
    report_progress(50, "status_subtitles")
    all_text_clips = []
    cumulative_duration = 0
    
    # Scale fonts based on resolution (Reference 720p)
    width_reference = 720 if request.platform == VideoPlatform.REEL else 1280
    scale_ratio = target_width / width_reference
    
    TEXT_MARGIN_X = int(target_width * 0.04) # Reduced margin for wider text
    TEXT_MAX_WIDTH = target_width - (2 * TEXT_MARGIN_X)
    
    ARABIC_FONT_SIZE = int(settings.FONT_SIZE * 0.7 * scale_ratio)
    ENGLISH_FONT_SIZE = int(settings.FONT_SIZE * 0.5 * scale_ratio)
    VERTICAL_SPACING = int(settings.FONT_SIZE * 0.5 * scale_ratio)
    TEXT_PADDING = int(60 * scale_ratio)
    TEXT_MARGIN = (int(10 * scale_ratio), int(10 * scale_ratio))
    
    TEXT_BLOCK_Y_CENTER = target_height / 2

    # Approximate char width for wrapping
    # Adjusted to 0.25 to utilize full width, especially in landscape
    ARABIC_CHAR_WIDTH_EST = ARABIC_FONT_SIZE * 0.25
    # Ensure at least 40 chars per line, but practically much higher now
    WRAP_WIDTH_CHARS = max(40, int(TEXT_MAX_WIDTH / ARABIC_CHAR_WIDTH_EST))

    if not os.path.exists(settings.ARABIC_FONT):
        cleanup_temp_dir(settings.TEMP_DIR)
        raise Exception(f"Arabic font file not found: {settings.ARABIC_FONT}")

    for info in ayah_clips_info:
        arabic_text_raw = info['arabic_text']
        english_text_raw = info['english_text']
        ayah_duration = info['duration']
        
        try:
            # TEXT FIX 1: formatting sends manually wrapped text
            arabic_text_formatted = formatArabicSentences(arabic_text_raw, width=WRAP_WIDTH_CHARS)
            
            # TEXT FIX 2: Add DOUBLE vertical padding (newlines + spaces) to safely clear descenders
            arabic_text_padded = f"\n\n {arabic_text_formatted} \n\n"
            
            arabic_clip = TextClip(
                text=arabic_text_padded,
                font_size=ARABIC_FONT_SIZE,
                font=settings.ARABIC_FONT,
                color=settings.ARABIC_FONT_COLOR,
                stroke_color='black',
                text_align='center',
                stroke_width=2,
                method='label', # TEXT FIX 3: 'label' respects our manual wrapping
                # size=(TEXT_MAX_WIDTH, None), # Remove size constraint for label, let it compute
                interline=int(30 * scale_ratio), # Increased line spacing (scaled)
                # margin=TEXT_MARGIN,
            )

            # English uses caption as it handles LTR wrapping fine
            english_clip = TextClip(
                text=english_text_raw,
                font_size=ENGLISH_FONT_SIZE,
                font=settings.ENGLISH_FONT,
                color=settings.ENGLISH_FONT_COLOR,
                stroke_color='black',
                text_align='center',
                stroke_width=1.5,
                method='caption',
                size=(TEXT_MAX_WIDTH, None),
                interline=8,
                margin=TEXT_MARGIN,
            )

            arabic_height = arabic_clip.h 
            english_height = english_clip.h + TEXT_PADDING
            total_text_block_height = arabic_height + english_height + VERTICAL_SPACING
            y_start_arabic = TEXT_BLOCK_Y_CENTER - (total_text_block_height / 2)
            english_y = y_start_arabic + arabic_height + VERTICAL_SPACING

            arabic_clip = arabic_clip.with_position(('center', y_start_arabic)) \
                                    .with_start(cumulative_duration) \
                                    .with_duration(ayah_duration)
            
            english_clip = english_clip.with_position(('center', english_y)) \
                                       .with_start(cumulative_duration) \
                                       .with_duration(ayah_duration)

            all_text_clips.extend([arabic_clip, english_clip])
            cumulative_duration += ayah_duration

        except Exception as e:
            cleanup_temp_dir(settings.TEMP_DIR)
            raise Exception(f"Error creating text clips: {str(e)}")

    # PHASE 4: Final Composition
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    report_progress(70, "status_rendering")
    
    logger.info(f"Total Video Duration Calculation: Audio={total_audio_duration}s, Background={background_clip.duration}s")
    
    try:
        final_video_clip = CompositeVideoClip([background_clip] + all_text_clips,
                                              size=(target_width, target_height))
        final_video_clip = final_video_clip.with_audio(concatenated_audio)
        
        # FORCE DURATION: Explicitly set and subclip to be safe
        final_video_clip = final_video_clip.with_duration(total_audio_duration)
        final_video_clip = final_video_clip.subclipped(0, total_audio_duration)
        
        logger.info(f"Final Export Duration: {final_video_clip.duration}s")
        
        # Optimize for Rendering on Free Tier (Low Memory/CPU)
        temp_audio_path = os.path.join(settings.TEMP_DIR, "temp-audio.m4a")

        # Setup Custom Logger
        video_logger = 'bar'
        if progress_callback:
            def rendering_progress(p=None, msg=None, **kwargs):
                if p is not None:
                    # Map rendering progress (0-100) to global progress (70-100)
                    global_p = 70 + int(p * 0.3)
                    # Instead of hardcoding, send key + percentage in a way frontend can parse?
                    # Easiest way: just send key "status_rendering" and frontend handles append
                    progress_callback(global_p, "status_rendering")
                elif msg:
                    # ignore internal messages
                    pass 
            video_logger = ProgressLogger(callback=rendering_progress)

        final_video_clip.write_videofile(
            output_filepath,
            fps=settings.FPS,
            codec=settings.VIDEO_CODEC,
            audio_codec=settings.AUDIO_CODEC,
            bitrate=settings.VIDEO_BITRATE,
            audio_bitrate=settings.AUDIO_BITRATE,
            logger=video_logger,
            temp_audiofile=temp_audio_path,
            remove_temp=True
        )
        
        report_progress(100, "status_completed")
        
        # Cleanup clips explicitly to free resources
        try:
            final_video_clip.close()
            # Explicitly close sub-clips if possible, though Composite logic handles some
            background_clip.close()
            concatenated_audio.close()
        except:
            pass
            
        return output_filepath

    except Exception as e:
        cleanup_temp_dir(settings.TEMP_DIR)
        raise Exception(f"Error during video export: {str(e)}")
