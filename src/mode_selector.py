"""
StyloMIDI - Mode Selector Dialog
Allows users to choose between MIDI and Keyboard modes
"""

from PyQt5 import QtWidgets

class ModeSelector(QtWidgets.QDialog):
    """Dialog for selecting application mode"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("StyloMIDI - Select Mode")
        self.setGeometry(300, 300, 300, 150)
        
        layout = QtWidgets.QVBoxLayout()
        
        # Mode options
        self.midi_radio = QtWidgets.QRadioButton("MIDI Mode")
        self.midi_radio.setChecked(True)
        self.keyboard_radio = QtWidgets.QRadioButton("Keyboard Mode")
        
        layout.addWidget(QtWidgets.QLabel("Select Operation Mode:"))
        layout.addWidget(self.midi_radio)
        layout.addWidget(self.keyboard_radio)
        
        # Description text
        midi_desc = QtWidgets.QLabel("MIDI Mode: Convert audio to MIDI signals")
        keyboard_desc = QtWidgets.QLabel("Keyboard Mode: Convert audio to keyboard keystrokes")
        midi_desc.setStyleSheet("color: gray; font-style: italic;")
        keyboard_desc.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(midi_desc)
        layout.addWidget(keyboard_desc)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.ok_button = QtWidgets.QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def get_selected_mode(self):
        """Return the selected mode"""
        if self.midi_radio.isChecked():
            return "midi"
        else:
            return "keyboard"