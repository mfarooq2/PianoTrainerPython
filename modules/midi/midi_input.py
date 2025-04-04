import pygame
import pygame.midi
from typing import List, Dict, Optional, Tuple, Callable, Set
import threading
import time

from modules.core.app_state import AppState


class MIDIInput:
    """
    Class for handling MIDI input devices.
    Detects MIDI devices, connects to them, and processes incoming MIDI events.
    """
    
    def __init__(self, app_state: AppState):
        """
        Initialize the MIDI input handler.
        
        Args:
            app_state: The application state object
        """
        self.app_state = app_state
        self.input_device: Optional[pygame.midi.Input] = None
        self.input_thread: Optional[threading.Thread] = None
        self.is_listening = False
        self.connected_device_id: Optional[int] = None
        self.connected_device_name: str = ""
        
        # Callbacks for MIDI events
        self.on_note_on: Optional[Callable[[int, int], None]] = None
        self.on_note_off: Optional[Callable[[int], None]] = None
        self.on_control_change: Optional[Callable[[int, int], None]] = None
        
        # Set to track currently pressed keys
        self.active_notes: Set[int] = set()
    
    def get_available_input_devices(self) -> List[Tuple[int, str]]:
        """
        Get a list of available MIDI input devices.
        
        Returns:
            List of (device_id, device_name) tuples
        """
        devices = []
        
        if not pygame.midi.get_init():
            return devices
            
        for i in range(pygame.midi.get_count()):
            info = pygame.midi.get_device_info(i)
            # Check if it's an input device (info[2] = is_input)
            if info[2]:
                device_id = i
                device_name = info[1].decode() if isinstance(info[1], bytes) else str(info[1])
                devices.append((device_id, device_name))
                
        return devices
    
    def connect_to_device(self, device_id: int = None) -> bool:
        """
        Connect to a specific MIDI input device or the default one.
        
        Args:
            device_id: ID of the device to connect to, or None for default
            
        Returns:
            True if connected successfully, False otherwise
        """
        # Disconnect from any existing device
        self.disconnect()
        
        # Check if Pygame MIDI is initialized
        if not pygame.midi.get_init():
            print("Error: Pygame MIDI not initialized")
            return False
            
        try:
            # Use provided device_id or get default
            if device_id is None:
                device_id = pygame.midi.get_default_input_id()
                if device_id == -1:
                    print("No default MIDI input device found")
                    return False
            
            # Validate device ID
            if device_id < 0 or device_id >= pygame.midi.get_count():
                print(f"Invalid MIDI device ID: {device_id}")
                return False
                
            # Make sure it's an input device
            device_info = pygame.midi.get_device_info(device_id)
            if not device_info[2]:  # is_input flag
                print(f"Device {device_id} is not an input device")
                return False
                
            # Connect to the device
            self.input_device = pygame.midi.Input(device_id)
            self.connected_device_id = device_id
            self.connected_device_name = device_info[1].decode() if isinstance(device_info[1], bytes) else str(device_info[1])
            
            print(f"Connected to MIDI input: {self.connected_device_name}")
            
            # Start the listening thread
            self.start_listening()
            return True
            
        except pygame.midi.MidiException as e:
            print(f"Error connecting to MIDI device: {e}")
            self.input_device = None
            self.connected_device_id = None
            self.connected_device_name = ""
            return False
    
    def disconnect(self):
        """Disconnect from the current MIDI input device."""
        self.stop_listening()
        
        if self.input_device:
            self.input_device.close()
            self.input_device = None
            
        print(f"Disconnected from MIDI input: {self.connected_device_name}")
        self.connected_device_id = None
        self.connected_device_name = ""
        self.active_notes.clear()
    
    def start_listening(self):
        """Start listening for MIDI events."""
        if not self.input_device or self.is_listening:
            return
            
        self.is_listening = True
        self.input_thread = threading.Thread(target=self._input_thread_func)
        self.input_thread.daemon = True
        self.input_thread.start()
        
        print("Started listening for MIDI events")
    
    def stop_listening(self):
        """Stop listening for MIDI events."""
        if self.is_listening:
            self.is_listening = False
            
            if self.input_thread and self.input_thread.is_alive():
                self.input_thread.join(timeout=1.0)
                
            print("Stopped listening for MIDI events")
    
    def _input_thread_func(self):
        """Thread function for reading MIDI input events."""
        if not self.input_device:
            self.is_listening = False
            return
            
        # Main listening loop
        while self.is_listening:
            if self.input_device.poll():
                # Read all available MIDI events (max 10 at a time to prevent blocking)
                events = self.input_device.read(10)
                for event in events:
                    self._process_midi_event(event)
                    
            # Small sleep to prevent CPU hogging
            time.sleep(0.001)
    
    def _process_midi_event(self, event):
        """
        Process a MIDI event from the input device.
        
        Args:
            event: MIDI event data from pygame.midi.Input.read()
        """
        # Extract event data
        # Pygame MIDI event format: [[status, data1, data2, data3], timestamp]
        midi_data = event[0]
        status = midi_data[0]
        
        # Extract the message type (high nibble) and channel (low nibble)
        message_type = status & 0xF0
        channel = status & 0x0F
        
        # Note On event (0x90-0x9F)
        if message_type == 0x90:
            note = midi_data[1]
            velocity = midi_data[2]
            
            # Some devices send Note On with velocity 0 instead of Note Off
                self._handle_note_on(note, velocity)
                self.active_notes.add(note)
            elif velocity == 0:
                self._handle_note_off(note)
                self.active_notes.discard(note)
                
        # Note Off event (0x80-0x8F)
        elif message_type == 0x80:
            note = midi_data[1]
            self._handle_note_off(note)
            self.active_notes.discard(note)
            
        # Control Change (0xB0-0xBF)
        elif message_type == 0xB0:
            control = midi_data[1]
            value = midi_data[2]
            self._handle_control_change(control, value)
    
    def _handle_note_on(self, note: int, velocity: int):
        """
        Handle a note-on MIDI event.
        
        Args:
            note: MIDI note number (0-127)
            velocity: Note velocity (1-127)
        """
        # Update app state with the pressed note
        self.app_state.handle_midi_note_on(note, velocity)
        
        # Call the callback if registered
        if self.on_note_on:
            self.on_note_on(note, velocity)
    
    def _handle_note_off(self, note: int):
        """
        Handle a note-off MIDI event.
        
        Args:
            note: MIDI note number (0-127)
        """
        # Update app state with the released note
        self.app_state.handle_midi_note_off(note)
        
        # Call the callback if registered
        if self.on_note_off:
            self.on_note_off(note)
    
    def _handle_control_change(self, control: int, value: int):
        """
        Handle a control change MIDI event.
        
        Args:
            control: Control number (0-127)
            value: Control value (0-127)
        """
        # Update app state with control change data
        self.app_state.handle_midi_control_change(control, value)
        
        # Call the callback if registered
        if self.on_control_change:
            self.on_control_change(control, value)
    
    def get_active_notes(self) -> Set[int]:
        """
        Get the set of currently active (pressed) MIDI notes.
        
        Returns:
            Set of active MIDI note numbers
        """
        return self.active_notes.copy()
    
    def is_connected(self) -> bool:
        """
        Check if connected to a MIDI input device.
        
        Returns:
            True if connected, False otherwise
        """
        return self.input_device is not None
    
    def get_connection_info(self) -> Tuple[Optional[int], str]:
        """
        Get information about the connected MIDI device.
        
        Returns:
            Tuple of (device_id, device_name) or (None, "") if not connected
        """
        return (self.connected_device_id, self.connected_device_name)

