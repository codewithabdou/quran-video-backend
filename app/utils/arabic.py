from moviepy import TextClip
from app.core.config import settings
import logging
from bidi.algorithm import get_display
import textwrap

logger = logging.getLogger(__name__)

def wrap_arabic_text(text, width=40):
    """
    Wraps Arabic text *before* reshaping to ensure correct line order.
    """
    wrapper = textwrap.TextWrapper(width=width)
    lines = wrapper.wrap(text)
    return lines

def formatArabicSentences(sentences, width=40):
    """
    Properly formats Arabic text for RTL display WHILE PRESERVING DIACRITICS.
    Now handles wrapping manually to prevent line-swapping issues in ImageMagick.
    """
    # 1. Wrap logical text first
    lines = wrap_arabic_text(sentences, width=width)
    
    formatted_lines = []
    
    ARABIC_FONT = settings.ARABIC_FONT
    
    # Configure Reshaper ONCE
    try:
        from arabic_reshaper import ArabicReshaper, config_for_true_type_font, ENABLE_ALL_LIGATURES
        
        try:
            config = config_for_true_type_font(ARABIC_FONT, ENABLE_ALL_LIGATURES)
            config['delete_harakat'] = False
            config['shift_harakat_position'] = False
            reshaper = ArabicReshaper(configuration=config)
            logger.debug("✓ Font-specific reshaping configured")
        except:
             # Fallback
            config = {
                'delete_harakat': False,
                'shift_harakat_position': False,
                'support_ligatures': True,
                'delete_tatweel': False,
                'support_zwj': True,
                'use_unshaped_instead_of_isolated': False,
            }
            reshaper = ArabicReshaper(configuration=config)
            logger.debug("✓ Manual reshaping configured")

        # 2. Reshape and BiDi each line INDIVIDUALLY
        for line in lines:
            reshaped = reshaper.reshape(line)
            bidi_line = get_display(reshaped)
            formatted_lines.append(bidi_line)
            
        # 3. Join with newlines (Top-down rendering for lines)
        return "\n".join(formatted_lines)
            
    except Exception as e:
        logger.error(f"Critical error in Arabic formatting: {e}")
        return sentences


