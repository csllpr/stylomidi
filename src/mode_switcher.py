"""
StyloMIDI - Mode Switcher
Helper module to handle mode switching without circular imports
"""

def switch_to_midi_mode(parent_window):
    """
    Switch from Keyboard mode to MIDI mode
    This function is designed to break circular imports
    
    Parameters:
    parent_window: The window instance to close before switching
    """
    # Stop any processing
    if hasattr(parent_window, 'stop_processing'):
        parent_window.stop_processing()
    
    # Close current window
    parent_window.close()
    
    # Import here to avoid circular imports
    from midi_mode import MidiModeWindow
    
    # Create and show new window
    midi_window = MidiModeWindow()
    midi_window.show()
    
    return midi_window

def switch_to_keyboard_mode(parent_window):
    """
    Switch from MIDI mode to Keyboard mode
    This function is designed to break circular imports
    
    Parameters:
    parent_window: The window instance to close before switching
    """
    # Stop any processing
    if hasattr(parent_window, 'stop_processing'):
        parent_window.stop_processing()
    
    # Close current window
    parent_window.close()
    
    # Import here to avoid circular imports
    from keyboard_mode import KeyboardModeWindow
    
    # Create and show new window
    keyboard_window = KeyboardModeWindow()
    keyboard_window.show()
    
    return keyboard_window