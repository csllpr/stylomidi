"""
StyloMIDI - MIDI Mode Window
Handles the GUI and functionality for MIDI mode
"""

import sys
import threading
import time
import pyaudio
import mido
from mido import Message
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt

from src.audio_processor import AudioProcessor

class MidiModeWindow(QtWidgets.QMainWindow):
    """Main window for MIDI mode"""
    note_detected_signal = QtCore.pyqtSignal(int)
    note_off_signal = QtCore.pyqtSignal()
    status_signal = QtCore.pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Audio setup
        self.buffer_size = 512
        self.sample_rate = 44100
        self.p = pyaudio.PyAudio()
        
        # Audio processor
        self.audio_processor = AudioProcessor(
            buffer_size=self.buffer_size,
            sample_rate=self.sample_rate
        )
        
        # Processing thread
        self.processing_thread = None
        self.running = False
        self.stream = None
        self.midi_output = None
        
        # Get available audio input devices
        self.audio_devices = []
        for i in range(self.p.get_device_count()):
            device_info = self.p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                self.audio_devices.append((i, device_info['name']))
        
        # Get available MIDI output ports
        self.midi_ports = mido.get_output_names()
        
        # Set up UI
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("StyloMIDI - MIDI Mode")
        self.setGeometry(100, 100, 600, 400)
        
        # Create central widget and layout
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Audio Input Device Selection
        audio_group = QtWidgets.QGroupBox("Audio Input")
        audio_layout = QtWidgets.QVBoxLayout()
        audio_group.setLayout(audio_layout)
        
        self.audio_device_combo = QtWidgets.QComboBox()
        for device_id, device_name in self.audio_devices:
            self.audio_device_combo.addItem(f"{device_name}", device_id)
        audio_layout.addWidget(QtWidgets.QLabel("Select Audio Input Device:"))
        audio_layout.addWidget(self.audio_device_combo)
        
        # MIDI Output Device Selection
        midi_group = QtWidgets.QGroupBox("MIDI Output")
        midi_layout = QtWidgets.QVBoxLayout()
        midi_group.setLayout(midi_layout)
        
        self.midi_port_combo = QtWidgets.QComboBox()
        if not self.midi_ports:
            self.midi_port_combo.addItem("No MIDI ports available")
        else:
            for port in self.midi_ports:
                self.midi_port_combo.addItem(port)
        midi_layout.addWidget(QtWidgets.QLabel("Select MIDI Output Port:"))
        midi_layout.addWidget(self.midi_port_combo)
        
        # MIDI Channel Selection
        self.midi_channel_combo = QtWidgets.QComboBox()
        for channel in range(16):
            self.midi_channel_combo.addItem(f"Channel {channel+1}", channel)
        midi_layout.addWidget(QtWidgets.QLabel("Select MIDI Channel:"))
        midi_layout.addWidget(self.midi_channel_combo)
        
        # Stability Settings
        stability_group = QtWidgets.QGroupBox("Pitch Stability")
        stability_layout = QtWidgets.QFormLayout()
        stability_group.setLayout(stability_layout)
        
        self.stability_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.stability_slider.setMinimum(1)
        self.stability_slider.setMaximum(20)
        self.stability_slider.setValue(self.audio_processor.required_stability)
        self.stability_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.stability_slider.setTickInterval(1)
        self.stability_slider.valueChanged.connect(self.update_stability)
        
        self.stability_value_label = QtWidgets.QLabel(str(self.audio_processor.required_stability))
        stability_layout.addRow("Required Stability:", self.stability_slider)
        stability_layout.addRow("Value:", self.stability_value_label)
        
        # Current note display
        self.note_display = QtWidgets.QLCDNumber()
        self.note_display.setDigitCount(3)
        self.note_display.display("---")
        self.note_display.setMinimumHeight(80)
        
        # Status bar
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Control buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        self.start_button = QtWidgets.QPushButton("Start")
        self.start_button.clicked.connect(self.start_processing)
        
        self.stop_button = QtWidgets.QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_processing)
        self.stop_button.setEnabled(False)
        
        self.switch_mode_button = QtWidgets.QPushButton("Switch to Keyboard Mode")
        self.switch_mode_button.clicked.connect(self.switch_to_keyboard_mode)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.switch_mode_button)
        
        # Add widgets to main layout
        main_layout.addWidget(audio_group)
        main_layout.addWidget(midi_group)
        main_layout.addWidget(stability_group)
        main_layout.addWidget(QtWidgets.QLabel("Current MIDI Note:"))
        main_layout.addWidget(self.note_display)
        main_layout.addLayout(button_layout)
        
        # Connect signals
        self.note_detected_signal.connect(self.update_note_display)
        self.note_off_signal.connect(self.clear_note_display)
        self.status_signal.connect(self.update_status)
        
        # Final UI adjustments
        self.show()
    
    def update_stability(self, value):
        self.audio_processor.set_stability(value)
        self.stability_value_label.setText(str(value))
    
    def update_note_display(self, note):
        self.note_display.display(note)
    
    def clear_note_display(self):
        self.note_display.display("---")
    
    def update_status(self, message):
        self.status_bar.showMessage(message)
    
    def switch_to_keyboard_mode(self):
        """Switch to keyboard mode"""
        self.stop_processing()
        self.close()
        # Import here to avoid circular imports
        from src.keyboard_mode import KeyboardModeWindow
        self.keyboard_window = KeyboardModeWindow()
        self.keyboard_window.show()
    
    def start_processing(self):
        try:
            # Check if MIDI ports are available
            if not self.midi_ports:
                QtWidgets.QMessageBox.critical(
                    self, 
                    "Error", 
                    "No MIDI output ports available. Please connect a MIDI device and restart the application."
                )
                return
            
            # Get selected device and port
            audio_device_id = self.audio_device_combo.currentData()
            midi_port_name = self.midi_port_combo.currentText()
            midi_channel = self.midi_channel_combo.currentData()
            
            # Open MIDI output
            self.midi_output = mido.open_output(midi_port_name)
            
            # Initialize pitch detector
            self.audio_processor.initialize_pitch_detector()
            
            # Open audio stream
            self.stream = self.p.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                input=True,
                input_device_index=audio_device_id,
                frames_per_buffer=self.buffer_size
            )
            
            # Reset state
            self.audio_processor.reset()
            self.current_note = None
            self.running = True
            
            # Start processing thread
            self.processing_thread = threading.Thread(target=self.process_audio, args=(midi_channel,))
            self.processing_thread.daemon = True
            self.processing_thread.start()
            
            # Update UI
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.audio_device_combo.setEnabled(False)
            self.midi_port_combo.setEnabled(False)
            self.midi_channel_combo.setEnabled(False)
            
            self.status_signal.emit("Processing started.")
        
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Could not start processing: {str(e)}")
    
    def stop_processing(self):
        if self.running:
            self.running = False
            if self.processing_thread:
                self.processing_thread.join(1.0)
            
            # Clean up
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            if self.midi_output:
                # Turn off any playing notes
                if self.current_note is not None:
                    self.midi_output.send(Message('note_off', note=self.current_note, channel=self.midi_channel_combo.currentData()))
                self.midi_output.close()
                self.midi_output = None
            
            # Update UI
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.audio_device_combo.setEnabled(True)
            self.midi_port_combo.setEnabled(True)
            self.midi_channel_combo.setEnabled(True)
            
            self.clear_note_display()
            self.status_signal.emit("Processing stopped.")
    
    def process_audio(self, midi_channel):
        try:
            while self.running:
                data = self.stream.read(self.buffer_size, exception_on_overflow=False)
                
                # Process audio buffer
                result = self.audio_processor.process_audio_buffer(data)
                
                if result['is_valid'] and result['midi_note'] is not None:
                    midi_note = result['midi_note']
                    
                    if result['is_new_note']:
                        # Turn off previous note if it exists
                        if self.current_note is not None:
                            self.midi_output.send(Message('note_off', note=self.current_note, channel=midi_channel))
                        
                        # Send new note
                        self.midi_output.send(Message('note_on', note=midi_note, velocity=64, channel=midi_channel))
                        self.status_signal.emit(f"Note: {midi_note}")
                        self.note_detected_signal.emit(midi_note)
                        
                        # Update current note
                        self.current_note = midi_note
                
                elif not result['is_valid'] and self.current_note is not None:
                    # If no valid signal, turn off current note
                    self.midi_output.send(Message('note_off', note=self.current_note, channel=midi_channel))
                    self.current_note = None
                    self.note_off_signal.emit()
        
        except Exception as e:
            self.status_signal.emit(f"Error: {str(e)}")
            self.running = False
    
    def closeEvent(self, event):
        self.stop_processing()
        if self.p:
            self.p.terminate()
        event.accept()