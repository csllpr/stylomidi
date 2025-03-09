import sys
import pyaudio
import aubio
import numpy as np
import mido
from mido import Message

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

current_note = None

def freq_to_midi(freq):
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
        
        if amplitude > 0.001 and freq > 20:
            note = freq_to_midi(freq)
            print(note)
            if note is not None:
                note = int(round(note))
                if note != current_note:
                    if current_note is not None:
                        midi_output.send(Message('note_off', note=current_note, channel=0))
                    midi_output.send(Message('note_on', note=note, velocity=64, channel=0))
                    print("Sent!")
                    current_note = note
        else:
            if current_note is not None:
                midi_output.send(Message('note_off', note=current_note, channel=0))
                current_note = None

except KeyboardInterrupt:
    print("Stopping...")
    stream.stop_stream()
    stream.close()
    p.terminate()
    midi_output.close()