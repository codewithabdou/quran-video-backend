from moviepy import TextClip
from app.core.config import settings
import logging
from bidi.algorithm import get_display

logger = logging.getLogger(__name__)

def formatArabicSentences(sentences):
    """
    Properly formats Arabic text for RTL display WHILE PRESERVING DIACRITICS.
    """
    try:
        from arabic_reshaper import ArabicReshaper, config_for_true_type_font, ENABLE_ALL_LIGATURES
        
        # Try method 1: Font-specific configuration (best quality)
        try:
            # This reads the TTF file and enables all supported ligatures
            config = config_for_true_type_font(
                settings.ARABIC_FONT,
                ENABLE_ALL_LIGATURES  # Enable all ligatures the font supports
            )
            
            # Override to preserve diacritics with proper positioning
            config['delete_harakat'] = False
            config['shift_harakat_position'] = False  # Critical for get_display()
            
            reshaper = ArabicReshaper(configuration=config)
            reshaped_text = reshaper.reshape(sentences)
            
        except (ImportError, Exception) as e:
             # Method 2: Manual configuration (fallback)
            configuration = {
                'delete_harakat': False,        # Keep diacritics
                'shift_harakat_position': True, # Shift for BiDi reversal
                'support_ligatures': True,      # Enable ligatures
                'delete_tatweel': False,
                'support_zwj': True,
                'use_unshaped_instead_of_isolated': False,
            }
            reshaper = ArabicReshaper(configuration=configuration)
            reshaped_text = reshaper.reshape(sentences)
        
        # Apply BiDi algorithm for RTL display
        bidi_text = get_display(reshaped_text)
        return bidi_text
            
    except Exception as e:
        logger.error(f"Critical error in Arabic formatting: {e}", exc_info=True)
        try:
            # Emergency fallback: basic reshaping (loses diacritics)
            import arabic_reshaper
            reshaped_text = arabic_reshaper.reshape(sentences)
            bidi_text = get_display(reshaped_text)
            return bidi_text
        except Exception:
            return sentences
