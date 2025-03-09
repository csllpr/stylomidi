import sys
import pyaudio
import aubio
import numpy as np
import mido
from mido import Message
import collections

# MIDI Setup
midi_output = mido.open_output(sys.argv[1])

# Audio Setup
buffer_size = 512
sample_rate = 44100
p = pyaudio.PyAudio()

# Aubio Pitch Detection
pitch_detector = aubio.pitch("default", 2048, buffer_size, sample_rate)
pitch_detector.set_unit("Hz")
pitch_detector.set_silence(-70)  # Silence threshold (dB)

# Open Audio Stream
stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=sample_rate,
                input=True,
                frames_per_buffer=buffer_size)

# Pitch stability parameters
note_history = collections.deque(maxlen=10)  # Store recent note detections
required_stability = 5  # Number of consistent readings required before changing note
stability_threshold = 2  # Maximum deviation allowed in semitones for "same note"
current_note = None
current_stable_note = None

def freq_to_midi(freq):
    """Convert frequency in Hz to MIDI note number"""
    if freq == 0:
        return None
    return int(69 + 12 * np.log2(freq / 440.0))

try:
    print("Starting...")
    while True:
        data = stream.read(buffer_size, exception_on_overflow=False)
        samples = np.frombuffer(data, dtype=aubio.float_type)
        
        freq = pitch_detector(samples)[0]
        amplitude = np.sum(samples**2) / len(samples)
        
        # Check if we have a valid signal
        if amplitude > 0.001 and freq > 20:
            note = freq_to_midi(freq)
            
            if note is not None:
                note = int(round(note))
                # Add to history
                note_history.append(note)
                
                # Check for stability
                if len(note_history) >= required_stability:
                    # Get the most common note in recent history
                    note_counts = collections.Counter(note_history)
                    most_common_note, count = note_counts.most_common(1)[0]
                    
                    # If the most common note appears frequently enough, consider it stable
                    if count >= required_stability:
                        # Only send MIDI if the stable note has changed
                        if most_common_note != current_stable_note:
                            # Turn off previous note if it exists
                            if current_note is not None:
                                midi_output.send(Message('note_off', note=current_note, channel=0))
                            
                            # Send new note
                            midi_output.send(Message('note_on', note=most_common_note, velocity=64, channel=0))
                            print(f"Stable note detected: {most_common_note}")
                            
                            # Update current notes
                            current_note = most_common_note
                            current_stable_note = most_common_note
        else:
            # If no valid signal, clear history and turn off current note
            note_history.clear()
            if current_note is not None:
                midi_output.send(Message('note_off', note=current_note, channel=0))
                current_note = None
                current_stable_note = None

except KeyboardInterrupt:
    print("Stopping...")
    stream.stop_stream()
    stream.close()
    p.terminate()
    midi_output.close()