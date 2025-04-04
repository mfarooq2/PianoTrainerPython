import pygame
import pygame.midi
from typing import Dict, List, Callable, Any, Optional, Tuple
from enum import Enum, auto

from modules.core.app_state import AppState, AppMode
from modules.midi.midi_input import MIDIInput


class EventType(Enum):
    """Enum defining different types of events the handler can process."""
    KEY_PRESS = auto()
    KEY_RELEASE = auto()
    MOUSE_CLICK = auto()
    MOUSE_MOVE = auto()
    MIDI_NOTE_ON = auto()
    MIDI_NOTE_OFF = auto()
    MIDI_CONTROL_CHANGE = auto()
    APP_QUIT = auto()
    MODE_CHANGE = auto()
    TIMER = auto()


class EventHandler:
    """
    Centralized event handler for the Piano Trainer application.
    Manages keyboard, mouse, and MIDI events and routes them to appropriate callbacks.
    """
    
    def __init__(self, app_state: AppState):
        """
        Initialize the event handler.
        
        Args:
            app_state: The application state object
        """
        self.app_state = app_state
        self.midi_input = None
        self.running = True
        
        # Dictionaries to store event callbacks
        self._event_callbacks: Dict[EventType, List[Callable[[Any], None]]] = {
            event_type: [] for event_type in EventType
        }
        
        # Key mapping for piano keys
        self.keyboard_to_note_mapping = {
            pygame.K_z: 48,  # C3
            pygame.K_s: 49,  # C#3
            pygame.K_x: 50,  # D3
            pygame.K_d: 51,  # D#3
            pygame.K_c: 52,  # E3
            pygame.K_v: 53,  # F3
            pygame.K_g: 54,  # F#3
            pygame.K_b: 55,  # G3
            pygame.K_h: 56,  # G#3
            pygame.K_n: 57,  # A3
            pygame.K_j: 58,  # A#3
            pygame.K_m: 59,  # B3
            pygame.K_COMMA: 60,  # C4 (middle C)
            pygame.K_l: 61,  # C#4
            pygame.K_PERIOD: 62,  # D4
            pygame.K_SEMICOLON: 63,  # D#4
            pygame.K_SLASH: 64,  # E4
            pygame.K_q: 60,  # C4 (middle C)
            pygame.K_2: 61,  # C#4
            pygame.K_w: 62,  # D4
            pygame.K_3: 63,  # D#4
            pygame.K_e: 64,  # E4
            pygame.K_r: 65,  # F4
            pygame.K_5: 66,  # F#4
            pygame.K_t: 67,  # G4
            pygame.K_6: 68,  # G#4
            pygame.K_y: 69,  # A4
            pygame.K_7: 70,  # A#4
            pygame.K_u: 71,  # B4
            pygame.K_i: 72,  # C5
            pygame.K_9: 73,  # C#5
            pygame.K_o: 74,  # D5
            pygame.K_0: 75,  # D#5
            pygame.K_p: 76,  # E5
            pygame.K_LEFTBRACKET: 77,  # F5
            pygame.K_EQUALS: 78,  # F#5
            pygame.K_RIGHTBRACKET: 79,  # G5
        }
        
        # Register default app-wide handlers
        self.register_callback(EventType.APP_QUIT, self._handle_quit)
    
    def init_midi_input(self, device_id: Optional[int] = None):
        """
        Initialize MIDI input.
        
        Args:
            device_id: Optional MIDI device ID to use. If None, will try to find a suitable device.
        """
        if pygame.midi.get_init():
            self.midi_input = MIDIInput(device_id)
            if self.midi_input.is_connected():
                print(f"Connected to MIDI device: {self.midi_input.get_device_name()}")
            else:
                print("Could not connect to MIDI device. Check connections and try again.")
    
    def register_callback(self, event_type: EventType, callback: Callable[[Any], None]):
        """
        Register a callback function for a specific event type.
        
        Args:
            event_type: The type of event to register for
            callback: The function to call when the event occurs
        """
        self._event_callbacks[event_type].append(callback)
    
    def unregister_callback(self, event_type: EventType, callback: Callable[[Any], None]):
        """
        Unregister a callback function for a specific event type.
        
        Args:
            event_type: The type of event to unregister from
            callback: The function to remove from callbacks
        """
        if callback in self._event_callbacks[event_type]:
            self._event_callbacks[event_type].remove(callback)
    
    def process_events(self):
        """Process all pending events in the queue."""
        for event in pygame.event.get():
            # Handle pygame events
            if event.type == pygame.QUIT:
                self._trigger_event(EventType.APP_QUIT, None)
            
            elif event.type == pygame.KEYDOWN:
                # Handle keyboard input for piano keys
                if event.key in self.keyboard_to_note_mapping:
                    note = self.keyboard_to_note_mapping[event.key]
                    self._trigger_event(EventType.MIDI_NOTE_ON, (note, 127))  # velocity 127 (max)
                
                # App control keys
                elif event.key == pygame.K_ESCAPE:
                    self._trigger_event(EventType.APP_QUIT, None)
                elif event.key == pygame.K_1:
                    self.app_state.set_mode(AppMode.FREESTYLE)
                    self._trigger_event(EventType.MODE_CHANGE, AppMode.FREESTYLE)
                elif event.key == pygame.K_2:
                    self.app_state.set_mode(AppMode.LEARNING)
                    self._trigger_event(EventType.MODE_CHANGE, AppMode.LEARNING)
                elif event.key == pygame.K_3:
                    self.app_state.set_mode(AppMode.ANALYSIS)
                    self._trigger_event(EventType.MODE_CHANGE, AppMode.ANALYSIS)
                
                # General key press event
                self._trigger_event(EventType.KEY_PRESS, event)
            
            elif event.type == pygame.KEYUP:
                # Handle releasing piano keys
                if event.key in self.keyboard_to_note_mapping:
                    note = self.keyboard_to_note_mapping[event.key]
                    self._trigger_event(EventType.MIDI_NOTE_OFF, (note, 0))  # velocity 0 (off)
                
                # General key release event
                self._trigger_event(EventType.KEY_RELEASE, event)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._trigger_event(EventType.MOUSE_CLICK, event)
            
            elif event.type == pygame.MOUSEMOTION:
                self._trigger_event(EventType.MOUSE_MOVE, event)
        
        # Process MIDI input if available
        if self.midi_input and self.midi_input.is_connected():
            for midi_event in self.midi_input.get_events():
                status, data1, data2 = midi_event[0][:3]
                
                # Note on event (status byte: 0x9n where n is the MIDI channel)
                if status >= 0x90 and status <= 0x9F and data2 > 0:
                    self._trigger_event(EventType.MIDI_NOTE_ON, (data1, data2))
                
                # Note off event (status byte: 0x8n or 0x9n with velocity 0)
                elif (status >= 0x80 and status <= 0x8F) or (status >= 0x90 and status <= 0x9F and data2 == 0):
                    self._trigger_event(EventType.MIDI_NOTE_OFF, (data1, 0))
                
                # Control change event (status byte: 0xBn)
                elif status >= 0xB0 and status <= 0xBF:
                    self._trigger_event(EventType.MIDI_CONTROL_CHANGE, (data1, data2))
    
    def _trigger_event(self, event_type: EventType, data: Any):
        """
        Trigger callbacks for a specific event type.
        
        Args:
            event_type: The type of event that occurred
            data: The data associated with the event
        """
        for callback in self._event_callbacks[event_type]:
            callback(data)
    
    def _handle_quit(self, _):
        """Handle application quit event."""
        self.running = False
        if self.midi_input:
            self.midi_input.close()
    
    def is_running(self) -> bool:
        """
        Check if the application should continue running.
        
        Returns:
            True if the application should continue, False otherwise
        """
        return self.running

