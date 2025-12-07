from PIL import Image, ImageDraw, ImageFont
import os
from app.core.config import settings

def create_text_image(text_arabic, text_english, output_path, width, height):
    """
    Generates a transparent PNG with Arabic and English text centered.
    """
    # Create transparent image
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Load Fonts (Fallback to default if not found, but we should have them)
    try:
        font_arabic = ImageFont.truetype(settings.ARABIC_FONT, settings.FONT_SIZE)
        font_english = ImageFont.truetype(settings.ENGLISH_FONT, int(settings.FONT_SIZE * 0.75))
    except IOError:
        # Fallback for dev/test if fonts missing
        font_arabic = ImageFont.load_default()
        font_english = ImageFont.load_default()

    # Calculate Sizes
    # PIL getbbox returns (left, top, right, bottom)
    bbox_arabic = draw.textbbox((0, 0), text_arabic, font=font_arabic)
    w_arabic = bbox_arabic[2] - bbox_arabic[0]
    h_arabic = bbox_arabic[3] - bbox_arabic[1]

    bbox_english = draw.textbbox((0, 0), text_english, font=font_english)
    w_english = bbox_english[2] - bbox_english[0]
    h_english = bbox_english[3] - bbox_english[1]

    # Center Vertically and Horizontally
    total_h = h_arabic + h_english + 40 # 40px spacing
    
    start_y = (height - total_h) // 2
    # Adjust for lower third if preferred (e.g. Reels style)
    # start_y = int(height * 0.7) - (total_h // 2)

    x_arabic = (width - w_arabic) // 2
    y_arabic = start_y
    
    x_english = (width - w_english) // 2
    y_english = y_arabic + h_arabic + 40

    # Draw Text with Shadow/Outline for visibility
    # Simulating stroke by drawing offsets
    stroke_width = 2
    stroke_color = "black"
    
    # Draw Arabic
    for adj in range(-stroke_width, stroke_width+1):
        for adj2 in range(-stroke_width, stroke_width+1):
             draw.text((x_arabic+adj, y_arabic+adj2), text_arabic, font=font_arabic, fill=stroke_color)
    draw.text((x_arabic, y_arabic), text_arabic, font=font_arabic, fill=settings.ARABIC_FONT_COLOR)

    # Draw English
    for adj in range(-stroke_width, stroke_width+1):
        for adj2 in range(-stroke_width, stroke_width+1):
             draw.text((x_english+adj, y_english+adj2), text_english, font=font_english, fill=stroke_color)
    draw.text((x_english, y_english), text_english, font=font_english, fill=settings.ENGLISH_FONT_COLOR)

    img.save(output_path, "PNG")
    return output_path
