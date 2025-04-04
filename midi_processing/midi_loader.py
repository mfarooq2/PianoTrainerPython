"""
MIDI File Loader and Processor

This module provides comprehensive functionality for loading, parsing, and analyzing MIDI files.
It extracts note events, metadata, and provides utilities for working with MIDI data in the 
Enhanced Piano Trainer application.
"""

import os
import logging
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
import mido
from mido import MidiFile, MidiTrack, Message

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class NoteEvent:
    """Represents a single MIDI note event with timing information"""
    note: int  # MIDI note number (0-127)
    velocity: int  # Note velocity (0-127)
    start_time: float  # Start time in seconds
    end_time: float  # End time in seconds
    track: int  # Track number
    channel: int  # MIDI channel

    @property
    def duration(self) -> float:
        """Return the duration of the note in seconds"""
        return self.end_time - self.start_time
    
    @property
    def is_black_key(self) -> bool:
        """Return True if this note is a black key on the piano"""
        return (self.note % 12) in [1, 3, 6, 8, 10]

@dataclass
class MidiMetadata:
    """Contains metadata information about a MIDI file"""
    filename: str
    format_type: int
    num_tracks: int
    ticks_per_beat: int
    total_time: float  # Total time in seconds
    time_signature: Tuple[int, int]  # numerator, denominator
    tempo: int  # in beats per minute
    key_signature: Optional[str] = None

class MidiLoader:
    """
    A class for loading and processing MIDI files.
    
    This class provides functionality to load MIDI files, extract note events,
    analyze MIDI content, and retrieve metadata about the file.
    """
    
    def __init__(self, midi_directory: Optional[str] = None):
        """
        Initialize the MIDI loader.
        
        Args:
            midi_directory: Optional path to a directory containing MIDI files.
        """
        self.midi_directory = midi_directory
        self.current_midi: Optional[MidiFile] = None
        self.current_file_path: Optional[str] = None
        self.note_events: List[NoteEvent] = []
        self.metadata: Optional[MidiMetadata] = None
    
    def get_available_midi_files(self) -> List[str]:
        """
        Get a list of available MIDI files in the specified directory.
        
        Returns:
            A list of MIDI filenames.
        """
        if not self.midi_directory or not os.path.exists(self.midi_directory):
            return []
        
        return [f for f in os.listdir(self.midi_directory) 
                if f.lower().endswith(('.mid', '.midi'))]
    
    def load_midi_file(self, file_path: str) -> bool:
        """
        Load a MIDI file from the specified path.
        
        Args:
            file_path: Path to the MIDI file to load.
            
        Returns:
            True if the file was loaded successfully, False otherwise.
        """
        try:
            self.current_midi = MidiFile(file_path)
            self.current_file_path = file_path
            self._extract_note_events()
            self._extract_metadata()
            return True
        except Exception as e:
            logger.error(f"Error loading MIDI file {file_path}: {e}")
            self.current_midi = None
            self.current_file_path = None
            self.note_events = []
            self.metadata = None
            return False
    
    def _extract_note_events(self) -> None:
        """
        Extract note events from the loaded MIDI file.
        
        This method processes the MIDI file and extracts all note-on and note-off events,
        matching them to create NoteEvent objects with timing information.
        """
        if not self.current_midi:
            return
        
        # Reset note events
        self.note_events = []
        
        # Keep track of active notes to match note_on with note_off events
        active_notes: Dict[Tuple[int, int, int], Tuple[int, float]] = {}  # (track, channel, note) -> (velocity, start_time)
        
        # Process each track
        for track_idx, track in enumerate(self.current_midi.tracks):
            absolute_time = 0.0
            
            for msg in track:
                # Convert tick time to seconds
                absolute_time += mido.tick2second(
                    msg.time, 
                    self.current_midi.ticks_per_beat, 
                    self._get_tempo_at_time(absolute_time)
                )
                
                # Process note on events (with velocity > 0)
                if msg.type == 'note_on' and msg.velocity > 0:
                    # Store the note as active
                    active_notes[(track_idx, msg.channel, msg.note)] = (msg.velocity, absolute_time)
                
                # Process note off events (note_off or note_on with velocity 0)
                elif (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0):
                    key = (track_idx, msg.channel, msg.note)
                    if key in active_notes:
                        velocity, start_time = active_notes[key]
                        
                        # Create a NoteEvent and add it to the list
                        note_event = NoteEvent(
                            note=msg.note,
                            velocity=velocity,
                            start_time=start_time,
                            end_time=absolute_time,
                            track=track_idx,
                            channel=msg.channel
                        )
                        
                        self.note_events.append(note_event)
                        del active_notes[key]
        
        # Sort note events by start time
        self.note_events.sort(key=lambda x: x.start_time)
    
    def _extract_metadata(self) -> None:
        """
        Extract metadata information from the loaded MIDI file.
        """
        if not self.current_midi or not self.current_file_path:
            return
        
        # Get filename without path
        filename = os.path.basename(self.current_file_path)
        
        # Calculate total time by finding the latest note end time
        total_time = 0.0
        if self.note_events:
            total_time = max(note.end_time for note in self.note_events)
        
        # Extract time signature and tempo
        time_signature = (4, 4)  # Default time signature
        tempo = 120  # Default tempo (BPM)
        key_signature = None
        
        for track in self.current_midi.tracks:
            for msg in track:
                if msg.type == 'time_signature':
                    time_signature = (msg.numerator, msg.denominator)
                elif msg.type == 'set_tempo':
                    # Convert tempo from microseconds per beat to BPM
                    tempo = int(60_000_000 / msg.tempo)
                elif msg.type == 'key_signature':
                    key_signature = msg.key
        
        self.metadata = MidiMetadata(
            filename=filename,
            format_type=self.current_midi.type,
            num_tracks=len(self.current_midi.tracks),
            ticks_per_beat=self.current_midi.ticks_per_beat,
            total_time=total_time,
            time_signature=time_signature,
            tempo=tempo,
            key_signature=key_signature
        )
    
    def _get_tempo_at_time(self, time_seconds: float) -> int:
        """
        Get the tempo at a specific time point in the MIDI file.
        This is a simplified implementation that doesn't handle tempo changes.
        
        Args:
            time_seconds: The time in seconds.
            
        Returns:
            The tempo in microseconds per beat.
        """
        # Default tempo: 500,000 microseconds per beat (120 BPM)
        tempo = 500000
        
        # TODO: Implement proper tempo tracking based on tempo change events
        
        return tempo
    
    def get_notes_in_time_range(self, start_time: float, end_time: float) -> List[NoteEvent]:
        """
        Get all note events that are active within the specified time range.
        
        Args:
            start_time: Start time in seconds.
            end_time: End time in seconds.
            
        Returns:
            A list of NoteEvent objects active in the time range.
        """
        return [note for note in self.note_events if 
                (note.start_time <= end_time and note.end_time >= start_time)]
    
    def get_notes_by_track(self, track_idx: int) -> List[NoteEvent]:
        """
        Get all note events for a specific track.
        
        Args:
            track_idx: The track index.
            
        Returns:
            A list of NoteEvent objects for the specified track.
        """
        return [note for note in self.note_events if note.track == track_idx]
    
    def get_notes_by_channel(self, channel: int) -> List[NoteEvent]:
        """
        Get all note events for a specific MIDI channel.
        
        Args:
            channel: The MIDI channel (0-15).
            
        Returns:
            A list of NoteEvent objects for the specified channel.
        """
        return [note for note in self.note_events if note.channel == channel]
    
    def get_highest_note(self) -> Optional[int]:
        """
        Get the highest note number in the MIDI file.
        
        Returns:
            The highest MIDI note number, or None if there are no notes.
        """
        if not self.note_events:
            return None
        return max(note.note for note in self.note_events)
    
    def get_lowest_note(self) -> Optional[int]:
        """
        Get the lowest note number in the MIDI file.
        
        Returns:
            The lowest MIDI note number, or None if there are no notes.
        """
        if not self.note_events:
            return None
        return min(note.note for note in self.note_events)
    
    def identify_key_signature(self) -> str:
        """
        Attempt to identify the key signature of the MIDI file based on note frequency.
        This is a simple implementation and may not be accurate for all pieces.
        
        Returns:
            A string representing the identified key signature.
        """
        if self.metadata and self.metadata.key_signature:
            return self.metadata.key_signature
        
        # TODO: Implement key signature detection algorithm based on note frequency
        
        return "Unknown"
    
    def get_note_name(self, note_number: int) -> str:
        """
        Convert a MIDI note number to its corresponding note name.
        
        Args:
            note_number: MIDI note number (0-127).
            
        Returns:
            String representation of the note (e.g., 'C4', 'F#5').
        """
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (note_number // 12) - 1
        note_idx = note_number % 12
        return f"{notes[note_idx]}{octave}"
    
    def get_note_number(self, note_name: str) -> int:
        """
        Convert a note name to its corresponding MIDI note number.
        
        Args:
            note_name: Note name string (e.g., 'C4', 'F#5').
            
        Returns:
            MIDI note number (0-127).
        """
        notes = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 
                'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 
                'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}
        
        # Extract note and octave
        if len(note_name) < 2:
            raise ValueError(f"Invalid note name: {note_name}")
        
        if note_name[1] == '#' or note_name[1] == 'b':
            if len(note_name) < 3:
                raise ValueError(f"Invalid note name: {note_name}")
            note = note_name[0:2]
            octave = int(note_name[2:])
        else:
            note = note_name[0]
            octave = int(note_name[1:])
        
        # Calculate MIDI note number
        if note not in notes:
            raise ValueError(f"Invalid note: {note}")
        
        return notes[note] + (octave + 1) * 12
    
    def extract_melodies(self, min_notes: int = 8) -> List[List[NoteEvent]]:
        """
        Extract potential melody lines from the MIDI file based on note patterns and duration.
        
        Args:
            min_notes: Minimum number of notes for a sequence to be considered a melody.
            
        Returns:
            A list of potential melodies, each represented as a list of NoteEvent objects.
        """
        # Sort notes by track and channel
        notes_by_track_channel = {}
        for note in self.note_events:
            key = (note.track, note.channel)
            if key not in notes_by_track_channel:
                notes_by_track_channel[key] = []
            notes_by_track_channel[key].append(note)
        
        # Find sequences that might be melodies
        melodies = []
        for track_channel, notes in notes_by_track_channel.items():
            if len(notes) < min_notes:
                continue
            
            # Further analysis could be done here to identify true melodies
            # For now, we'll just consider any sequence with enough notes
            melodies.append(notes)
        
        return melodies
    
    def extract_chords(self, max_start_diff: float = 0.05) -> List[List[NoteEvent]]:
        """
        Extract chords from the MIDI file by grouping notes that start at approximately the same time.
        
        Args:
            max_start_diff: Maximum difference in start times (in seconds) for notes to be considered part of the same chord.
            
        Returns:
            A list of chords, each represented as a list of NoteEvent objects.
        """
        if not self.note_events:
            return []
        
        # Sort notes by start time
        sorted_notes = sorted(self.note_events, key=lambda x: x.start_time)
        
        chords = []
        current_chord = [sorted_

