"""
StyloMIDI - Keyboard Emulator Module
Handles keyboard mapping and emulation
"""

import csv
import os

class KeyboardEmulator:
    """Emulates keyboard presses based on detected notes"""
    def __init__(self):
        # Import here to avoid dependency if not using keyboard mode
        try:
            import keyboard
            self.keyboard = keyboard
            self.available = True
        except ImportError:
            self.available = False
            print("Keyboard module not available. Please install with: pip install keyboard")
        
        self.current_key = None
        self.note_to_key_map = {}
    
    def load_mapping(self, config_file):
        """
        Load note-to-key mapping from CSV file
        
        Parameters:
        config_file (str): Path to CSV mapping file
        
        Returns:
        bool: True if successful, False otherwise
        """
        self.note_to_key_map = {}
        
        try:
            with open(config_file, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        note_name = row[0].strip()
                        key = row[1].strip()
                        # Convert note name to MIDI number
                        midi_note = self.note_name_to_midi(note_name)
                        if midi_note is not None:
                            self.note_to_key_map[midi_note] = key
            return True
        except Exception as e:
            print(f"Error loading mapping: {str(e)}")
            return False
    
    def note_name_to_midi(self, note_name):
        """
        Convert note name (e.g., 'C4') to MIDI note number
        
        Parameters:
        note_name (str): Note name in format like 'C4', 'F#3', etc.
        
        Returns:
        int: MIDI note number, or None if invalid
        """
        # Note name to semitone mapping
        notes = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
                 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 
                 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}
        
        # Extract note and octave
        if len(note_name) < 2:
            return None
        
        # Handle sharp/flat notes
        if len(note_name) >= 3 and (note_name[1] == '#' or note_name[1] == 'b'):
            note = note_name[:2]
            try:
                octave = int(note_name[2:])
            except ValueError:
                return None
        else:
            note = note_name[0]
            try:
                octave = int(note_name[1:])
            except ValueError:
                return None
        
        # Calculate MIDI note number
        if note in notes:
            return notes[note] + (octave + 1) * 12
        return None
    
    def press_key(self, midi_note):
        """
        Press key corresponding to MIDI note
        
        Parameters:
        midi_note (int): MIDI note number
        
        Returns:
        bool: True if key was pressed, False if not mapped or not available
        """
        if not self.available or midi_note not in self.note_to_key_map:
            return False
        
        key = self.note_to_key_map[midi_note]
        
        # Release previous key if different
        if self.current_key is not None and self.current_key != key:
            self.keyboard.release(self.current_key)
        
        # Press new key
        if key != self.current_key:
            self.keyboard.press(key)
            self.current_key = key
        
        return True
    
    def release_key(self):
        """Release currently pressed key"""
        if not self.available or self.current_key is None:
            return
        
        self.keyboard.release(self.current_key)
        self.current_key = None
    
    def create_default_config(self, config_dir):
        """
        Create a default configuration file in the specified directory
        
        Parameters:
        config_dir (str): Directory path
        
        Returns:
        str: Path to created file
        """
        # Create config directory if it doesn't exist
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        # Create a sample config file
        sample_file = os.path.join(config_dir, "default_config.csv")
        with open(sample_file, 'w') as f:
            f.write("C4,a\nD4,s\nE4,d\nF4,f\nG4,g\nA4,h\nB4,j\nC5,k\n")
            f.write("# Format: [Note][Octave], [Key]\n")
            f.write("# Example: C4, a (maps middle C to the 'a' key)\n")
        
        return sample_file
    
    def get_mapping_info(self):
        """
        Get human-readable information about current mapping
        
        Returns:
        str: Formatted mapping text
        """
        if not self.note_to_key_map:
            return "No mapping loaded"
        
        mapping_text = "MIDI Note\tKey\n"
        mapping_text += "-----------------\n"
        
        # Sort by MIDI note for better display
        sorted_mapping = sorted(self.note_to_key_map.items())
        for note, key in sorted_mapping:
            mapping_text += f"{note}\t{key}\n"
        
        return mapping_text