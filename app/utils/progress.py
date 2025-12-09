from proglog import ProgressBarLogger

class ProgressLogger(ProgressBarLogger):
    def __init__(self, callback=None):
        super().__init__()
        self.callback = callback
        self.last_message = ""

    def callback_trait(self, **changes):
        # We don't use this general one much, bars_callback is better
        pass

    def bars_callback(self, bar, attr, value, old_value=None):
        if self.callback:
            # Check for any active bar with a valid total
            if bar in self.bars and self.bars[bar]['total'] > 0:
                # Calculate percentage for this bar
                current = value
                total = self.bars[bar]['total']
                percentage = int((current / total) * 100)
                
                # Report any bar that is providing metric updates (frame_index, t, chunk, etc.)
                self.callback(percentage, f"Rendering: {percentage}%")
    
    def log(self, message):
        # Capture generic log messages if needed
        # We silence these for the frontend to avoid "percentage: null" noise
        # if self.callback:
        #     self.callback(None, message)
        pass
