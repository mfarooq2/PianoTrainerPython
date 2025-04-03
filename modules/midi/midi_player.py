import pygame
import pygame.midi
import mido
from typing import List, Dict, Optional, Tuple, Callable
import threading
import time
import os
from dataclasses import dataclass

from modules.core.app_state import AppState


@dataclass
class MidiNote:
    """Represents a MIDI note from a MIDI file."""
    note: int
    velocity: int
    start_time: float
    end_time: float
    channel: int
    is_playing: bool = False
    
    @property
    def duration(self) -> float:
        """Get the duration of the note in seconds."""
        return self.end_time - self.start_time


class MIDIPlayer:
    """
    Class for handling MIDI file playback.
    Parses MIDI files and manages note playback timing.
    """
    
    def __init__(self, app_state: AppState):
        """
        Initialize the MIDI player.
        
        Args:
            app_state: The application state object
        """
        self.app_state = app_state
        self.midi_file: Optional[mido.MidiFile] = None
        self.notes: List[MidiNote] = []
        self.notes_by_start_time: Dict[float, List[MidiNote]] = {}
        self.playback_thread: Optional[threading.Thread] = None
        self.is_playing = False
        self.current_position = 0.0  # Position in seconds
        self.playback_speed = 1.0
        self.output_device: Optional[pygame.midi.Output] = None
        self.on_note_on: Optional[Callable[[int, int], None]] = None
        self.on_note_off: Optional[Callable[[int], None]] = None
        
        # Try to initialize MIDI output
        self._init_midi_output()
    
    def _init_midi_output(self):
        """Initialize MIDI output device."""
        if pygame.midi.get_init():
            try:
                default_output_id = pygame.midi.get_default_output_id()
                if default_output_id != -1:
                    self.output_device = pygame.midi.Output(default_output_id)
                    print(f"Connected to MIDI output: {pygame.midi.get_device_info(default_output_id)[1].decode()}")
                else:
                    print("No default MIDI output device found.")
            except pygame.midi.MidiException as e:
                print(f"Error initializing MIDI output: {e}")
    
    def load_midi_file(self, filepath: str) -> bool:
        """
        Load and parse a MIDI file.
        
        Args:
            filepath: Path to the MIDI file
            
        Returns:
            True if file was loaded successfully, False otherwise
        """
        if not os.path.exists(filepath):
            print(f"Error: MIDI file not found: {filepath}")
            return False
        
        try:
            # Load the MIDI file
            self.midi_file = mido.MidiFile(filepath)
            self.notes = []
            self.notes_by_start_time = {}
            
            # Parse the file and extract notes
            self._parse_midi_file()
            
            print(f"Loaded MIDI file: {os.path.basename(filepath)}")
            print(f"  Tracks: {len(self.midi_file.tracks)}")
            print(f"  Notes: {len(self.notes)}")
            print(f"  Duration: {self.get_duration():.2f} seconds")
            
            # Reset playback position
            self.current_position = 0.0
            return True
            
        except Exception as e:
            print(f"Error loading MIDI file: {e}")
            return False
    
    def _parse_midi_file(self):
        """Parse the loaded MIDI file and extract notes."""
        if not self.midi_file:
            return
        
        tempo = 500000  # Default tempo (microseconds per beat)
        current_time = 0.0  # Time in seconds
        active_notes = {}  # Dict to track note on events {(note, channel): start_time}
        
        # Process all events in all tracks
        for track in self.midi_file.tracks:
            track_time = 0.0
            
            for msg in track:
                # Convert delta time to seconds
                delta_seconds = mido.tick2second(msg.time, self.midi_file.ticks_per_beat, tempo)
                track_time += delta_seconds
                
                # Set tempo if tempo event
                if msg.type == 'set_tempo':
                    tempo = msg.tempo
                
                # Handle note on events
                elif msg.type == 'note_on' and msg.velocity > 0:
                    note_key = (msg.note, msg.channel)
                    active_notes[note_key] = track_time
                
                # Handle note off events
                elif (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0):
                    note_key = (msg.note, msg.channel)
                    
                    if note_key in active_notes:
                        start_time = active_notes[note_key]
                        end_time = track_time
                        
                        note = MidiNote(
                            note=msg.note,
                            velocity=127,  # Use max velocity for note-off events
                            start_time=start_time,
                            end_time=end_time,
                            channel=msg.channel
                        )
                        
                        # Add to notes list
                        self.notes.append(note)
                        
                        # Group by start time for efficient playback
                        if start_time not in self.notes_by_start_time:
                            self.notes_by_start_time[start_time] = []
                        self.notes_by_start_time[start_time].append(note)
                        
                        # Remove from active notes
                        del active_notes[note_key]
    
    def get_duration(self) -> float:
        """Get the total duration of the MIDI file in seconds."""
        if not self.notes:
            return 0.0
        return max(note.end_time for note in self.notes)
    
    def play(self, from_position: float = None):
        """
        Start playback of the MIDI file.
        
        Args:
            from_position: Optional position in seconds to start from
        """
        if not self.notes or self.is_playing:
            return
            
        if from_position is not None:
            self.current_position = max(0.0, min(from_position, self.get_duration()))
        
        self.is_playing = True
        self.playback_thread = threading.Thread(target=self._playback_thread_func)
        self.playback_thread.daemon = True
        self.playback_thread.start()
        
        print(f"Playback started at position {self.current_position:.2f}s")
    
    def pause(self):
        """Pause the MIDI playback."""
        if self.is_playing:
            self.is_playing = False
            print("Playback paused")
    
    def stop(self):
        """Stop the MIDI playback and reset position."""
        self.is_playing = False
        self.current_position = 0.0
        
        # Turn off any playing notes
        self._all_notes_off()
        print("Playback stopped")
    
    def set_playback_speed(self, speed: float):
        """
        Set the playback speed.
        
        Args:
            speed: Playback speed multiplier (1.0 = normal speed)
        """
        self.playback_speed = max(0.1, min(speed, 2.0))
        print(f"Playback speed set to {self.playback_speed:.1f}x")
    
    def _playback_thread_func(self):
        """Thread function for MIDI playback."""
        if not self.notes:
            self.is_playing = False
            return
            
        # Get a sorted list of all start times for efficient iteration
        start_times = sorted(self.notes_by_start_time.keys())
        
        # Find the first start time that's >= current_position
        start_idx = 0
        while start_idx < len(start_times) and start_times[start_idx] < self.current_position:
            start_idx += 1
            
        # Reset all notes' playing status
        for note in self.notes:
            note.is_playing = False
            
        # Get the start time for the loop
        start_time = time.time()
        adjusted_position = self.current_position
        
        # Main playback loop
        while self.is_playing and start_idx < len(start_times):
            current_time = time.time()
            elapsed = (current_time - start_time) * self.playback_speed
            self.current_position = adjusted_position + elapsed
            
            # Process all notes that should start by current_position
            while start_idx < len(start_times) and start_times[start_idx] <= self.current_position:
                time_point = start_times[start_idx]
                for note in self.notes_by_start_time[time_point]:
                    # Start the note
                    self._note_on(note.note, note.velocity, note.channel)
                    note.is_playing = True
                    
                    # Schedule note off based on duration
                    off_time = note.end_time - self.current_position
                    if off_time > 0:
                        threading.Timer(off_time / self.playback_speed, 
                                       self._note_off, args=[note.note, note.channel]).start()
                start_idx += 1
                
            # Check if we've reached the end
            if start_idx >= len(start_times):
                # Check for any remaining notes to finish
                latest_end = max(note.end_time for note in self.notes)
                if self.current_position >= latest_end:
                    self.is_playing = False
                    self.current_position = 0.0
                    print("Playback finished")
                
            time.sleep(0.001)  # Small sleep to prevent CPU hogging
            
    def _note_on(self, note: int, velocity: int, channel: int):
        """
        Send note-on MIDI message.
        
        Args:
            note: MIDI note number (0-127)
            velocity: Note velocity (0-127)
            channel: MIDI channel (0-15)
        """
        if self.output_device:
            try:
                self.output_device.note_on(note, velocity, channel)
            except Exception as e:
                print(f"Error sending note-on: {e}")
                
        # Call the note_on callback if registered
        if self.on_note_on:
            self.on_note_on(note, velocity)
    
    def _note_off(self, note: int, channel: int):
        """
        Send note-off MIDI message.
        
        Args:
            note: MIDI note number (0-127)
            channel: MIDI channel (0-15)
        """
        if self.output_device:
            try:
                self.output_device.note_off(note, 0, channel)
            except Exception as e:
                print(f"Error sending note-off: {e}")
                
        # Call the note_off callback if registered
        if self.on_note_off:
            self.on_note_off(note)
    
    def _all_notes_off(self):
        """Turn off all MIDI notes on all channels."""
        if self.output_device:
            # Send all notes off on all 16 channels
            for channel in range(16):
                try:
                    # Controller 123 = All Notes Off
                    self.output_device.write_short(0xB0 + channel, 123, 0)
                except Exception as e:
                    print(f"Error sending all-notes-off: {e}")
    
    def register_note_callbacks(self, 
                                on_note_on: Callable[[int, int], None], 
                                on_note_off: Callable[[int], None]):
        """
        Register callbacks for note on/off events.
        
        Args:
            on_note_on: Callback function for note-on events (note, velocity)
            on_note_off: Callback function for note-off events (note)
        """
        self.on_note_on = on_note_on
        self.on_note_off = on_note_off
    
    def get_active_notes(self) -> List[int]:
        """Get a list of currently active (playing) notes."""
        return [note.note for note in self.notes if note.is_playing]
    
    def cleanup(self):
        """Clean up resources."""
        self.is_playing = False
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=1.0)
            
        self._all_notes_off()
        
        if self.output_device:
            self.output_device.close()
            self.output_device = None
