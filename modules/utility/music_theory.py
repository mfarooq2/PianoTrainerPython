"""
Music Theory Module for Piano Trainer

This module provides music theory utilities such as note name conversion,
scale and chord generation, and chord progression analysis.
"""

from enum import Enum
from typing import List, Dict, Tuple, Optional, Union


# Define constants for notes
NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
FLAT_NOTES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
NOTE_TO_NUMBER = {note: i for i, note in enumerate(NOTES)}
FLAT_NOTE_TO_NUMBER = {note: i for i, note in enumerate(FLAT_NOTES)}

# Define scale intervals (half steps from root)
SCALE_INTERVALS = {
    'major': [0, 2, 4, 5, 7, 9, 11],
    'natural_minor': [0, 2, 3, 5, 7, 8, 10],
    'harmonic_minor': [0, 2, 3, 5, 7, 8, 11],
    'melodic_minor': [0, 2, 3, 5, 7, 9, 11],
    'dorian': [0, 2, 3, 5, 7, 9, 10],
    'phrygian': [0, 1, 3, 5, 7, 8, 10],
    'lydian': [0, 2, 4, 6, 7, 9, 11],
    'mixolydian': [0, 2, 4, 5, 7, 9, 10],
    'locrian': [0, 1, 3, 5, 6, 8, 10],
    'pentatonic_major': [0, 2, 4, 7, 9],
    'pentatonic_minor': [0, 3, 5, 7, 10],
    'blues': [0, 3, 5, 6, 7, 10],
    'whole_tone': [0, 2, 4, 6, 8, 10],
    'chromatic': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
}

# Define chord intervals (half steps from root)
CHORD_INTERVALS = {
    'major': [0, 4, 7],
    'minor': [0, 3, 7],
    'diminished': [0, 3, 6],
    'augmented': [0, 4, 8],
    'sus2': [0, 2, 7],
    'sus4': [0, 5, 7],
    'major_7': [0, 4, 7, 11],
    'minor_7': [0, 3, 7, 10],
    'dominant_7': [0, 4, 7, 10],
    'diminished_7': [0, 3, 6, 9],
    'half_diminished_7': [0, 3, 6, 10],
    'augmented_7': [0, 4, 8, 10],
    'major_9': [0, 4, 7, 11, 14],
    'minor_9': [0, 3, 7, 10, 14],
    'dominant_9': [0, 4, 7, 10, 14],
    'major_6': [0, 4, 7, 9],
    'minor_6': [0, 3, 7, 9],
    'add9': [0, 4, 7, 14],
    'minor_add9': [0, 3, 7, 14]
}

# Roman numeral mapping for chord progression analysis
ROMAN_NUMERALS = {
    0: 'I',
    1: 'II',
    2: 'III',
    3: 'IV',
    4: 'V',
    5: 'VI',
    6: 'VII'
}


class ChordQuality(Enum):
    MAJOR = "major"
    MINOR = "minor"
    DIMINISHED = "diminished"
    AUGMENTED = "augmented"


class MusicTheory:
    """Class providing music theory utilities."""
    
    @staticmethod
    def midi_to_note(midi_num: int, use_flats: bool = False) -> str:
        """
        Convert MIDI note number to note name.
        
        Args:
            midi_num: MIDI note number (0-127)
            use_flats: If True, use flat notation (e.g., Bb instead of A#)
            
        Returns:
            Note name with octave (e.g., 'C4', 'F#5')
        """
        if not 0 <= midi_num <= 127:
            raise ValueError(f"MIDI note number must be between 0 and 127, got {midi_num}")
            
        octave = (midi_num // 12) - 1
        note_idx = midi_num % 12
        
        if use_flats:
            note = FLAT_NOTES[note_idx]
        else:
            note = NOTES[note_idx]
            
        return f"{note}{octave}"
    
    @staticmethod
    def note_to_midi(note_str: str) -> int:
        """
        Convert note name to MIDI note number.
        
        Args:
            note_str: Note name with octave (e.g., 'C4', 'F#5', 'Bb3')
            
        Returns:
            MIDI note number (0-127)
        """
        if len(note_str) < 2:
            raise ValueError(f"Invalid note format: {note_str}")
            
        # Handle both flat and sharp notations
        note_name = note_str[:-1]  # Extract note without octave
        octave = int(note_str[-1])  # Extract octave
        
        if note_name in NOTE_TO_NUMBER:
            note_idx = NOTE_TO_NUMBER[note_name]
        elif note_name in FLAT_NOTE_TO_NUMBER:
            note_idx = FLAT_NOTE_TO_NUMBER[note_name]
        else:
            raise ValueError(f"Unknown note name: {note_name}")
            
        return (octave + 1) * 12 + note_idx
    
    @staticmethod
    def normalize_note(note_name: str) -> str:
        """
        Normalize note name (handle enharmonic equivalents).
        
        Args:
            note_name: Note name (e.g., 'C#', 'Db')
            
        Returns:
            Normalized note name (using sharps notation)
        """
        # Handle notes with octave numbers
        if note_name[-1].isdigit():
            octave = note_name[-1]
            name = note_name[:-1]
            if name in NOTE_TO_NUMBER:
                return f"{name}{octave}"
            elif name in FLAT_NOTE_TO_NUMBER:
                idx = FLAT_NOTE_TO_NUMBER[name]
                return f"{NOTES[idx]}{octave}"
        # Handle notes without octave numbers
        else:
            if note_name in NOTE_TO_NUMBER:
                return note_name
            elif note_name in FLAT_NOTE_TO_NUMBER:
                idx = FLAT_NOTE_TO_NUMBER[note_name]
                return NOTES[idx]
                
        raise ValueError(f"Unknown note name: {note_name}")
    
    @staticmethod
    def get_scale(root: str, scale_type: str, octave: Optional[int] = None) -> List[str]:
        """
        Generate a scale based on root note and scale type.
        
        Args:
            root: Root note (e.g., 'C', 'F#')
            scale_type: Type of scale (e.g., 'major', 'natural_minor')
            octave: Optional octave number to include in the output
            
        Returns:
            List of notes in the scale
        """
        if scale_type not in SCALE_INTERVALS:
            raise ValueError(f"Unknown scale type: {scale_type}")
            
        # Normalize root note and get index
        if root in NOTE_TO_NUMBER:
            root_idx = NOTE_TO_NUMBER[root]
        elif root in FLAT_NOTE_TO_NUMBER:
            root_idx = FLAT_NOTE_TO_NUMBER[root]
        else:
            raise ValueError(f"Unknown root note: {root}")
            
        # Generate scale notes
        scale = []
        for interval in SCALE_INTERVALS[scale_type]:
            note_idx = (root_idx + interval) % 12
            note = NOTES[note_idx]
            
            if octave is not None:
                # Handle octave wrapping
                additional_octave = (root_idx + interval) // 12
                note_octave = octave + additional_octave
                note = f"{note}{note_octave}"
                
            scale.append(note)
            
        return scale
    
    @staticmethod
    def get_chord(root: str, chord_type: str, octave: Optional[int] = None) -> List[str]:
        """
        Generate a chord based on root note and chord type.
        
        Args:
            root: Root note (e.g., 'C', 'F#')
            chord_type: Type of chord (e.g., 'major', 'minor_7')
            octave: Optional octave number to include in the output
            
        Returns:
            List of notes in the chord
        """
        if chord_type not in CHORD_INTERVALS:
            raise ValueError(f"Unknown chord type: {chord_type}")
            
        # Normalize root note and get index
        if root in NOTE_TO_NUMBER:
            root_idx = NOTE_TO_NUMBER[root]
        elif root in FLAT_NOTE_TO_NUMBER:
            root_idx = FLAT_NOTE_TO_NUMBER[root]
        else:
            raise ValueError(f"Unknown root note: {root}")
            
        # Generate chord notes
        chord = []
        for interval in CHORD_INTERVALS[chord_type]:
            note_idx = (root_idx + interval) % 12
            note = NOTES[note_idx]
            
            if octave is not None:
                # Handle octave wrapping
                additional_octave = (root_idx + interval) // 12
                note_octave = octave + additional_octave
                note = f"{note}{note_octave}"
                
            chord.append(note)
            
        return chord
    
    @staticmethod
    def recognize_chord(notes: List[str]) -> Tuple[Optional[str], Optional[str]]:
        """
        Recognize chord type from a list of notes.
        
        Args:
            notes: List of notes (e.g., ['C', 'E', 'G'])
            
        Returns:
            Tuple of (root_note, chord_type) or (None, None) if not recognized
        """
        if not notes:
            return None, None
            
        # Normalize notes and get indices
        normalized_notes = [MusicTheory.normalize_note(note) for note in notes]
        
        # Remove octave information if present
        clean_notes = []
        for note in normalized_notes:
            if note[-1].isdigit():
                clean_notes.append(note[:-1])
            else:
                clean_notes.append(note)
                
        # Try each note as potential root
        for root in clean_notes:
            root_idx = NOTE_TO_NUMBER[root]
            
            # Calculate intervals from root
            intervals = []
            for note in clean_notes:
                note_idx = NOTE_TO_NUMBER[note]
                interval = (note_idx - root_idx) % 12
                intervals.append(interval)
                
            intervals.sort()
            
            # Check against known chord types
            for chord_type, chord_intervals in CHORD_INTERVALS.items():
                if len(intervals) == len(chord_intervals) and intervals == chord_intervals:
                    return root, chord_type
                    
        return None, None
    
    @staticmethod
    def analyze_chord_progression(chords: List[List[str]], key: str) -> List[str]:
        """
        Analyze a chord progression relative to a key.
        
        Args:
            chords: List of chords, each a list of notes
            key: The key to analyze against (e.g., 'C')
            
        Returns:
            List of Roman numeral analysis for the progression
        """
        if not chords:
            return []
            
        # Get key index
        if key in NOTE_TO_NUMBER:
            key_idx = NOTE_TO_NUMBER[key]
        elif key in FLAT_NOTE_TO_NUMBER:
            key_idx = FLAT_NOTE_TO_NUMBER[key]
        else:
            raise ValueError(f"Unknown key: {key}")
            
        # Get scale degrees in the key
        major_scale = MusicTheory.get_scale(key, 'major')
        scale_degrees = [NOTE_TO_NUMBER[note] for note in major_scale]
        
        result = []
        for chord_notes in chords:
            # Identify chord
            root, chord_type = MusicTheory.recognize_chord(chord_notes)
            
            if root is None or chord_type is None:
                result.append("?")
                continue
                
            # Get scale degree
            root_idx = NOTE_TO_NUMBER[root]
            degree = (root_idx - key_idx) % 12
            
            # Find position in the scale
            if degree in scale_degrees:
                roman_idx = scale_degrees.index(degree)
                roman = ROMAN_NUMERALS[roman_idx]
                
                # Adjust for chord quality
                if chord_type == 'minor' or chord_type.startswith('minor_'):
                    roman = roman.lower()
                elif chord_type == 'diminished' or chord_type.startswith('diminished_'):
                    roman = roman.lower() + '°'
                elif chord_type == 'augmented' or chord_type.startswith('augmented_'):
                    roman = roman + '+'
                    
                # Add seventh notation if needed
                if chord_type.endswith('7') or chord_type.endswith('_7'):
                    roman = roman + '7'
                    
                result.append(roman)
            else:
                # Non-diatonic chord
                result.append(f"{root}({chord_type})")
                
        return result

