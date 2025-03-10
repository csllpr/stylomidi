"""
StyloMIDI - Audio Processing Module
Handles all audio input processing and pitch detection
"""

import collections
import numpy as np
import aubio

class AudioProcessor:
    """Handles audio processing and pitch detection"""
    def __init__(self, buffer_size=512, sample_rate=44100, stability_threshold=5):
        # Audio parameters
        self.buffer_size = buffer_size
        self.sample_rate = sample_rate
        
        # Pitch stability parameters
        self.note_history = collections.deque(maxlen=10)
        self.required_stability = stability_threshold
        self.current_note = None
        self.current_stable_note = None
        
        # Create pitch detector
        self.pitch_detector = None
    
    def initialize_pitch_detector(self):
        """Initialize the pitch detector"""
        self.pitch_detector = aubio.pitch("default", 2048, self.buffer_size, self.sample_rate)
        self.pitch_detector.set_unit("Hz")
        self.pitch_detector.set_silence(-70)
    
    def process_audio_buffer(self, audio_data):
        """
        Process audio buffer and detect stable pitch
        
        Parameters:
        audio_data (bytes): Raw audio data from audio stream
        
        Returns:
        dict: Processing result with keys:
            - is_valid: True if valid audio detected
            - midi_note: MIDI note number if stable note detected, None otherwise
            - is_new_note: True if this is a new stable note
            - freq: Raw frequency detected
            - amplitude: Audio amplitude
        """
        # Convert to numpy array
        samples = np.frombuffer(audio_data, dtype=aubio.float_type)
        
        # Get pitch and amplitude
        freq = self.pitch_detector(samples)[0]
        amplitude = np.sum(samples**2) / len(samples)
        
        result = {
            'is_valid': False,
            'midi_note': None,
            'is_new_note': False,
            'freq': freq,
            'amplitude': amplitude
        }
        
        # Check if we have a valid signal
        if amplitude > 0.001 and freq > 20:
            note = self.freq_to_midi(freq)
            
            if note is not None:
                note = int(round(note))
                # Add to history
                self.note_history.append(note)
                
                # Check for stability
                if len(self.note_history) >= self.required_stability:
                    # Get the most common note in recent history
                    note_counts = collections.Counter(self.note_history)
                    most_common_note, count = note_counts.most_common(1)[0]
                    
                    # If the most common note appears frequently enough, consider it stable
                    if count >= self.required_stability:
                        result['is_valid'] = True
                        result['midi_note'] = most_common_note
                        
                        # Check if this is a new stable note
                        if most_common_note != self.current_stable_note:
                            result['is_new_note'] = True
                            self.current_stable_note = most_common_note
        else:
            # If no valid signal, clear history
            self.note_history.clear()
            self.current_stable_note = None
        
        return result
    
    def set_stability(self, value):
        """Set the required stability threshold"""
        self.required_stability = value
    
    def reset(self):
        """Reset the processor state"""
        self.note_history.clear()
        self.current_note = None
        self.current_stable_note = None
    
    @staticmethod
    def freq_to_midi(freq):
        """Convert frequency in Hz to MIDI note number"""
        if freq == 0:
            return None
        return int(69 + 12 * np.log2(freq / 440.0))