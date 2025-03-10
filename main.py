#!/usr/bin/env python3
"""
StyloMIDI - Main Application Entry Point
Converts audio input to MIDI signals or keyboard inputs
"""

import sys
from PyQt5 import QtWidgets
from src.mode_selector import ModeSelector
from src.midi_mode import MidiModeWindow
from src.keyboard_mode import KeyboardModeWindow

def main():
    """Main application entry point"""
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')  # Consistent style across platforms
    
    # Show mode selector dialog
    mode_selector = ModeSelector()
    if mode_selector.exec_() == QtWidgets.QDialog.Accepted:
        selected_mode = mode_selector.get_selected_mode()
        
        # Launch appropriate window based on selected mode
        if selected_mode == "midi":
            window = MidiModeWindow()
        else:
            window = KeyboardModeWindow()
        
        # Show window and run application
        window.show()
        sys.exit(app.exec_())
    else:
        # User canceled, exit application
        sys.exit(0)

if __name__ == "__main__":
    main()