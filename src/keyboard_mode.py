"""
StyloMIDI - Keyboard Mode Window (Debug Version)
Handles the GUI and functionality for Keyboard mode with enhanced error reporting
"""

import sys
import os
import threading
import time
import traceback
import pyaudio
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt

# Add explicit debug logging
def log_error(error_message):
    """Write error message to log file"""
    log_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(log_dir, "stylomidi_error.log")
    
    with open(log_file, "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {error_message}\n")

try:
    # Import with explicit error handling
    from src.audio_processor import AudioProcessor
    from src.keyboard_emulator import KeyboardEmulator
except Exception as e:
    error_msg = f"Import error: {str(e)}\n{traceback.format_exc()}"
    log_error(error_msg)
    raise

class KeyboardModeWindow(QtWidgets.QMainWindow):
    """Main window for keyboard mode"""
    note_detected_signal = QtCore.pyqtSignal(int)
    note_off_signal = QtCore.pyqtSignal()
    status_signal = QtCore.pyqtSignal(str)
    
    def __init__(self):
        try:
            super().__init__()
            
            # Log initialization
            log_error("Initializing KeyboardModeWindow")
            
            # Audio setup
            self.buffer_size = 512
            self.sample_rate = 44100
            self.p = pyaudio.PyAudio()
            
            # Audio processor
            self.audio_processor = AudioProcessor(
                buffer_size=self.buffer_size,
                sample_rate=self.sample_rate
            )
            
            # Keyboard emulator
            self.keyboard_emulator = KeyboardEmulator()
            
            # Processing thread
            self.processing_thread = None
            self.running = False
            self.stream = None
            
            # Get available audio input devices
            self.audio_devices = []
            for i in range(self.p.get_device_count()):
                device_info = self.p.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    self.audio_devices.append((i, device_info['name']))
            
            # Config directory setup
            self.config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
            log_error(f"Config directory: {self.config_dir}")
            self.config_files = self.scan_config_files()
            
            # Set up UI
            log_error("Setting up UI")
            self.init_ui()
            log_error("UI setup complete")
            
        except Exception as e:
            error_msg = f"Initialization error: {str(e)}\n{traceback.format_exc()}"
            log_error(error_msg)
            QtWidgets.QMessageBox.critical(None, "Error", f"Error initializing Keyboard Mode:\n\n{str(e)}")
            raise
    
    def scan_config_files(self):
        """Scan config directory for CSV mapping files"""
        try:
            config_files = []
            
            # Create config directory if it doesn't exist
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
                log_error(f"Created config directory: {self.config_dir}")
                
                # Create a sample config file
                sample_file = self.keyboard_emulator.create_default_config(self.config_dir)
                config_files.append(("default_config.csv", sample_file))
            else:
                # Scan existing files
                log_error(f"Scanning config directory: {self.config_dir}")
                for filename in os.listdir(self.config_dir):
                    if filename.lower().endswith('.csv'):
                        full_path = os.path.join(self.config_dir, filename)
                        config_files.append((filename, full_path))
                        log_error(f"Found config file: {filename}")
                
                # If no config files found, create a default one
                if not config_files:
                    log_error("No config files found, creating default")
                    sample_file = self.keyboard_emulator.create_default_config(self.config_dir)
                    config_files.append(("default_config.csv", sample_file))
            
            return config_files
        except Exception as e:
            error_msg = f"Config scan error: {str(e)}\n{traceback.format_exc()}"
            log_error(error_msg)
            raise
    
    def init_ui(self):
        try:
            self.setWindowTitle("StyloMIDI - Keyboard Mode")
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
            
            # Key Mapping Selection
            mapping_group = QtWidgets.QGroupBox("Key Mapping")
            mapping_layout = QtWidgets.QVBoxLayout()
            mapping_group.setLayout(mapping_layout)
            
            self.mapping_combo = QtWidgets.QComboBox()
            for filename, filepath in self.config_files:
                self.mapping_combo.addItem(filename, filepath)
            
            mapping_layout.addWidget(QtWidgets.QLabel("Select Key Mapping:"))
            mapping_layout.addWidget(self.mapping_combo)
            
            # Add button to open config directory
            self.open_config_dir_button = QtWidgets.QPushButton("Open Config Directory")
            self.open_config_dir_button.clicked.connect(self.open_config_directory)
            mapping_layout.addWidget(self.open_config_dir_button)
            
            # Refresh button for config files
            self.refresh_config_button = QtWidgets.QPushButton("Refresh Config Files")
            self.refresh_config_button.clicked.connect(self.refresh_config_files)
            mapping_layout.addWidget(self.refresh_config_button)
            
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
            
            # Current key display
            self.key_display = QtWidgets.QLabel("None")
            self.key_display.setAlignment(Qt.AlignCenter)
            self.key_display.setStyleSheet("font-size: 24px; font-weight: bold;")
            self.key_display.setMinimumHeight(50)
            
            # Mapping display area
            self.mapping_display = QtWidgets.QTextEdit()
            self.mapping_display.setReadOnly(True)
            self.mapping_display.setMinimumHeight(100)
            
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
            
            self.switch_mode_button = QtWidgets.QPushButton("Switch to MIDI Mode")
            self.switch_mode_button.clicked.connect(self.switch_to_midi_mode)
            
            button_layout.addWidget(self.start_button)
            button_layout.addWidget(self.stop_button)
            button_layout.addWidget(self.switch_mode_button)
            
            # Add widgets to main layout
            main_layout.addWidget(audio_group)
            main_layout.addWidget(mapping_group)
            main_layout.addWidget(stability_group)
            main_layout.addWidget(QtWidgets.QLabel("Current MIDI Note:"))
            main_layout.addWidget(self.note_display)
            main_layout.addWidget(QtWidgets.QLabel("Current Key:"))
            main_layout.addWidget(self.key_display)
            main_layout.addWidget(QtWidgets.QLabel("Mapping:"))
            main_layout.addWidget(self.mapping_display)
            main_layout.addLayout(button_layout)
            
            # Connect signals
            self.note_detected_signal.connect(self.update_note_display)
            self.note_off_signal.connect(self.clear_note_display)
            self.status_signal.connect(self.update_status)
            self.mapping_combo.currentIndexChanged.connect(self.load_selected_mapping)
            
            # Load initial mapping
            self.load_selected_mapping()
            
        except Exception as e:
            error_msg = f"UI initialization error: {str(e)}\n{traceback.format_exc()}"
            log_error(error_msg)
            raise
    
    def update_stability(self, value):
        """Update stability threshold"""
        self.audio_processor.set_stability(value)
        self.stability_value_label.setText(str(value))
    
    def update_note_display(self, note):
        """Update note display and key display"""
        try:
            self.note_display.display(note)
            
            # Update key display
            if note in self.keyboard_emulator.note_to_key_map:
                key = self.keyboard_emulator.note_to_key_map[note]
                self.key_display.setText(key)
            else:
                self.key_display.setText("Not mapped")
        except Exception as e:
            log_error(f"Update note display error: {str(e)}")
    
    def clear_note_display(self):
        """Clear note and key displays"""
        try:
            self.note_display.display("---")
            self.key_display.setText("None")
        except Exception as e:
            log_error(f"Clear note display error: {str(e)}")
    
    def update_status(self, message):
        """Update status bar message"""
        try:
            self.status_bar.showMessage(message)
            log_error(f"Status: {message}")
        except Exception as e:
            log_error(f"Update status error: {str(e)}")
    
    def open_config_directory(self):
        """Open the config directory in file explorer"""
        try:
            if sys.platform == 'win32':
                os.startfile(self.config_dir)
            elif sys.platform == 'darwin':  # macOS
                os.system(f'open "{self.config_dir}"')
            else:  # Linux
                os.system(f'xdg-open "{self.config_dir}"')
        except Exception as e:
            log_error(f"Open config directory error: {str(e)}")
            QtWidgets.QMessageBox.warning(self, "Error", f"Could not open config directory:\n{str(e)}")
    
    def refresh_config_files(self):
        """Refresh the list of config files"""
        try:
            self.config_files = self.scan_config_files()
            
            # Update combobox
            self.mapping_combo.clear()
            for filename, filepath in self.config_files:
                self.mapping_combo.addItem(filename, filepath)
            
            self.load_selected_mapping()
        except Exception as e:
            log_error(f"Refresh config files error: {str(e)}")
            QtWidgets.QMessageBox.warning(self, "Error", f"Could not refresh config files:\n{str(e)}")
    
    def load_selected_mapping(self):
        """Load the selected mapping file"""
        try:
            if self.mapping_combo.count() == 0:
                self.mapping_display.setText("No mapping files found")
                return
            
            filepath = self.mapping_combo.currentData()
            if filepath and os.path.exists(filepath):
                # Load mapping into the keyboard emulator
                if self.keyboard_emulator.load_mapping(filepath):
                    # Display mapping in the text area
                    mapping_text = self.keyboard_emulator.get_mapping_info()
                    self.mapping_display.setText(mapping_text)
                    self.status_signal.emit(f"Loaded mapping: {self.mapping_combo.currentText()}")
                else:
                    self.mapping_display.setText(f"Error loading mapping file: {filepath}")
            else:
                self.mapping_display.setText(f"File not found: {filepath}")
        except Exception as e:
            error_msg = f"Load mapping error: {str(e)}\n{traceback.format_exc()}"
            log_error(error_msg)
            self.mapping_display.setText(f"Error: {str(e)}")
    
    def switch_to_midi_mode(self):
        """Switch to MIDI mode"""
        try:
            self.stop_processing()
            self.close()
            # Import here to avoid circular imports
            log_error("Attempting to switch to MIDI mode")
            from midi_mode import MidiModeWindow
            self.midi_window = MidiModeWindow()
            self.midi_window.show()
        except Exception as e:
            error_msg = f"Switch to MIDI mode error: {str(e)}\n{traceback.format_exc()}"
            log_error(error_msg)
            QtWidgets.QMessageBox.critical(None, "Error", f"Could not switch to MIDI mode:\n\n{str(e)}")
    
    def start_processing(self):
        try:
            # Check if keyboard module is available
            if not self.keyboard_emulator.available:
                QtWidgets.QMessageBox.critical(
                    self, 
                    "Error", 
                    "Keyboard module not available. Please install with: pip install keyboard"
                )
                return
            
            # Get selected device
            audio_device_id = self.audio_device_combo.currentData()
            
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
            self.processing_thread = threading.Thread(target=self.process_audio)
            self.processing_thread.daemon = True
            self.processing_thread.start()
            
            # Update UI
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.audio_device_combo.setEnabled(False)
            self.mapping_combo.setEnabled(False)
            self.refresh_config_button.setEnabled(False)
            
            self.status_signal.emit("Processing started.")
        
        except Exception as e:
            error_msg = f"Start processing error: {str(e)}\n{traceback.format_exc()}"
            log_error(error_msg)
            QtWidgets.QMessageBox.critical(self, "Error", f"Could not start processing:\n\n{str(e)}")
    
    def stop_processing(self):
        try:
            if self.running:
                self.running = False
                if self.processing_thread:
                    self.processing_thread.join(1.0)
                
                # Clean up
                if self.stream:
                    self.stream.stop_stream()
                    self.stream.close()
                    self.stream = None
                
                # Release any pressed keys
                self.keyboard_emulator.release_key()
                
                # Update UI
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.audio_device_combo.setEnabled(True)
                self.mapping_combo.setEnabled(True)
                self.refresh_config_button.setEnabled(True)
                
                self.clear_note_display()
                self.status_signal.emit("Processing stopped.")
        except Exception as e:
            log_error(f"Stop processing error: {str(e)}")
    
    def process_audio(self):
        try:
            while self.running:
                data = self.stream.read(self.buffer_size, exception_on_overflow=False)
                
                # Process audio buffer
                result = self.audio_processor.process_audio_buffer(data)
                
                if result['is_valid'] and result['midi_note'] is not None:
                    midi_note = result['midi_note']
                    
                    if result['is_new_note']:
                        # Press the corresponding key
                        key_pressed = self.keyboard_emulator.press_key(midi_note)
                        
                        if key_pressed:
                            self.status_signal.emit(f"Note: {midi_note} -> Key: {self.keyboard_emulator.current_key}")
                        else:
                            self.status_signal.emit(f"Note: {midi_note} (not mapped)")
                        
                        self.note_detected_signal.emit(midi_note)
                        
                        # Update current note
                        self.current_note = midi_note
                
                elif not result['is_valid'] and self.current_note is not None:
                    # If no valid signal, release key
                    self.keyboard_emulator.release_key()
                    self.current_note = None
                    self.note_off_signal.emit()
        
        except Exception as e:
            error_msg = f"Audio processing error: {str(e)}\n{traceback.format_exc()}"
            log_error(error_msg)
            self.status_signal.emit(f"Error: {str(e)}")
            self.running = False
    
    def closeEvent(self, event):
        try:
            self.stop_processing()
            if self.p:
                self.p.terminate()
            event.accept()
        except Exception as e:
            log_error(f"Close event error: {str(e)}")
            event.accept()

# Test code to directly run this window (for debugging)
if __name__ == "__main__":
    try:
        app = QtWidgets.QApplication(sys.argv)
        app.setStyle('Fusion')
        window = KeyboardModeWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        error_msg = f"Main execution error: {str(e)}\n{traceback.format_exc()}"
        log_error(error_msg)
        QtWidgets.QMessageBox.critical(None, "Error", f"Application error:\n\n{str(e)}")