"""
Music Theory Module for Piano Trainer Application.

Provides utility functions for working with musical notes, scales, and chords.
"""
from enum import Enum
from typing import List, Dict, Tuple, Set, Optional
import re


# Define note names with enharmonic equivalents
NOTE_NAMES = ['C', 'C#/Db', 'D', 'D#/Eb', 'E', 'F', 'F#/Gb', 'G', 'G#/Ab', 'A', 'A#/Bb', 'B']
SHARP_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
FLAT_NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']


class NotePreference(Enum):
    """Preference for how to name notes (with sharps or flats)"""
    SHARPS = 0
    FLATS = 1
    STANDARD = 2  # Use standard notation for key signatures


class ScaleType(Enum):
    """Types of scales supported by the application"""
    MAJOR = 'major'
    NATURAL_MINOR = 'natural_minor'
    HARMONIC_MINOR = 'harmonic_minor'
    MELODIC_MINOR = 'melodic_minor'
    BLUES = 'blues'
    PENTATONIC_MAJOR = 'pentatonic_major'
    PENTATONIC_MINOR = 'pentatonic_minor'
    CHROMATIC = 'chromatic'
    DORIAN = 'dorian'
    PHRYGIAN = 'phrygian'
    LYDIAN = 'lydian'
    MIXOLYDIAN = 'mixolydian'
    LOCRIAN = 'locrian'


class ChordType(Enum):
    """Types of chords supported by the application"""
    MAJOR = 'major'
    MINOR = 'minor'
    DIMINISHED = 'diminished'
    AUGMENTED = 'augmented'
    DOMINANT_7TH = 'dominant_7th'
    MAJOR_7TH = 'major_7th'
    MINOR_7TH = 'minor_7th'
    HALF_DIMINISHED_7TH = 'half_diminished_7th'
    DIMINISHED_7TH = 'diminished_7th'
    AUGMENTED_7TH = 'augmented_7th'
    SUSPENDED_2ND = 'suspended_2nd'
    SUSPENDED_4TH = 'suspended_4th'
    MAJOR_6TH = 'major_6th'
    MINOR_6TH = 'minor_6th'
    NINTH = 'ninth'


# Scale intervals (semitones from root)
SCALE_INTERVALS = {
    ScaleType.MAJOR: [0, 2, 

