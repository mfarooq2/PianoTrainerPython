import pygame
import random
from typing import List, Dict, Tuple, Optional, Set
import time
import numpy as np
from enum import Enum


class NoteStatus(Enum):
    """Enumeration of possible note statuses."""

    FALLING = 0  # Note is falling
    HIT = 1  # Note was correctly played
    MISSED = 2  # Note was missed
    WRONG = 3  # Wrong note was played
    EXPIRED = 4  # Note has moved off screen


class Note:
    """Class representing a single falling note in the learning mode."""

    def __init__(
        self,
        note_number,
        start_time,
        speed,
        screen_height,
        target_y,
        velocity: int = 64,
        duration: float = 0.5,
    ):
        """
        Initialize a falling note.

        Args:
            note_number (int): MIDI note number
            start_time (float): Time when the note started falling
            speed (float): Speed of the falling note in pixels per second
            screen_height (int): Height of the screen
            target_y (int): Y position where the note should be hit
            velocity (int): Note velocity (0-127)
            duration (float): Note duration in seconds
        """
        self.note_number = note_number
        self.start_time = start_time
        self.speed = speed
        self.screen_height = screen_height
        self.target_y = target_y
        self.velocity = velocity
        self.duration = duration
        self.status = NoteStatus.FALLING
        self.color = (100, 149, 237)  # Cornflower blue
        self.hit_time = None
        self.y_pos = 0  # y position
        self.height = 20
        self.hit = False
        self.missed = False
        self.should_be_removed = False

        # Timing window for "perfect" and "good" hits
        self.perfect_window = 0.05  # seconds
        self.good_window = 0.15  # seconds

    def update(self, current_time):
        """
        Update the note's position based on elapsed time.

        Args:
            current_time (float): Current time in seconds

        Returns:
            bool: True if the note is still active, False if it should be removed
        """
        if self.status == NoteStatus.FALLING:
            # Calculate the y position based on elapsed time
            elapsed = current_time - self.start_time
            self.y = elapsed * self.speed
            self.y_pos = self.y

            # Check if note has moved past the target
            if self.y > self.screen_height:
                self.status = NoteStatus.EXPIRED
                return False

        # Keep hit/missed notes on screen for a short time
        elif self.status in (NoteStatus.HIT, NoteStatus.MISSED, NoteStatus.WRONG):
            if current_time - self.hit_time > 0.5:  # Remove after 0.5 seconds
                return False

        return True

    def check_hit(self, note_number, current_time):
        """
        Check if the note was hit correctly.

        Args:
            note_number (int): MIDI note number that was played
            current_time (float): Current time in seconds

        Returns:
            tuple: (hit_status, score) where hit_status is one of:
                   "perfect", "good", "miss", "wrong", or None
                   and score is the point value (0 for miss/wrong)
        """
        if self.status != NoteStatus.FALLING:
            return None, 0

        # Calculate timing error (distance from target)
        elapsed = current_time - self.start_time
        expected_time = self.target_y / self.speed
        timing_error = abs(elapsed - expected_time)

        # Check if the correct note was played
        if note_number == self.note_number:
            self.hit_time = current_time
            self.hit = True

            # Check timing
            if timing_error <= self.perfect_window:
                self.status = NoteStatus.HIT
                self.color = (0, 255, 0)  # Green for perfect
                return "perfect", 100
            elif timing_error <= self.good_window:
                self.status = NoteStatus.HIT
                self.color = (255, 255, 0)  # Yellow for good
                return "good", 50
            else:
                # Too early or too late, but still the right note
                self.status = NoteStatus.HIT
                self.color = (255, 165, 0)  # Orange for hit but timing off
                return "hit", 25
        else:
            # Wrong note
            self.status = NoteStatus.WRONG
            self.color = (255, 0, 0)  # Red for wrong note
            self.hit_time = current_time
            return "wrong", 0

    def mark_as_missed(self, current_time):
        """
        Mark the note as missed (not played in time).

        Args:
            current_time (float): Current time in seconds
        """
        if self.status == NoteStatus.FALLING:
            self.status = NoteStatus.MISSED
            self.missed = True
            self.color = (128, 128, 128)  # Gray for missed
            self.hit_time = current_time

    def update_position(
        self, current_time: float, fall_speed: float, pause_time: float = 0
    ):
        """
        Update the y position of this note based on the current time.

        Args:
            current_time: Current time in seconds
            fall_speed: Speed at which notes fall (pixels per second)
            pause_time: Total time the note generator has been paused
        """
        # Adjust for any pause time
        effective_time = current_time - pause_time
        time_diff = effective_time - self.start_time

        # Calculate position based on time difference and fall speed
        self.y_pos = time_diff * fall_speed

    def should_be_played(self, current_time: float, pause_time: float = 0) -> bool:
        """
        Determine if this note should be played at the current time.

        Args:
            current_time: Current time in seconds
            pause_time: Total time the note generator has been paused

        Returns:
            True if the note should be played, False otherwise
        """
        effective_time = current_time - pause_time
        return effective_time >= self.start_time and not self.hit and not self.missed


class NoteGenerator:
    """
    Class responsible for generating and managing falling notes in the learning mode.
    """

    def __init__(self, config, midi_player):
        """
        Initialize the note generator.

        Args:
            config (Config): Application configuration
            midi_player (MIDIPlayer): MIDI player instance
        """
        self.config = config
        self.midi_player = midi_player
        self.screen_width = config.screen_width
        self.screen_height = config.screen_height
        self.piano_height = config.piano_height

        # Target y-position is at the top of the piano
        self.target_y = self.screen_height - self.piano_height

        # Speed of falling notes in pixels per second
        self.note_speed = 200  # Adjust based on difficulty

        # List of active falling notes
        self.active_notes = []

        # Queue of upcoming notes from the MIDI file
        self.note_queue = []

        # Track learning mode stats
        self.score = 0
        self.perfect_hits = 0
        self.good_hits = 0
        self.hits = 0
        self.misses = 0
        self.wrong_notes = 0
        self.hit_notes: Set[int] = set()  # Track hit notes

        # Time management
        self.start_time = None
        self.current_time = None
        self.paused = False
        self.pause_start_time = None
        self.total_pause_time = 0
        self.fall_distance = self.target_y
        self.fall_speed = self.note_speed

        # Initialize the note queue from midi data
        self._parse_midi_data()

    def _parse_midi_data(self):
        """Parse MIDI data to create upcoming notes."""
        self.note_queue = []

        for event in self.midi_player.midi_data:
            if event["type"] == "note_on" and event["velocity"] > 0:
                note = Note(
                    note_number=event["note"],
                    start_time=event["time"],
                    speed=self.note_speed,
                    screen_height=self.screen_height,
                    target_y=self.target_y,
                    velocity=event["velocity"],
                    duration=0.5,  # Default, will be updated
                )
                self.note_queue.append(note)

        # Sort by time
        self.note_queue.sort(key=lambda x: x.start_time)

    def start(self):
        """Start the note generator and reset statistics."""
        self.start_time = time.time()
        self.current_time = self.start_time
        self.active_notes = []

        # Reset stats
        self.score = 0
        self.perfect_hits = 0
        self.good_hits = 0
        self.hits = 0
        self.misses = 0
        self.wrong_notes = 0
        self.hit_notes = set()

        self.paused = False
        self.total_pause_time = 0

        # Re-parse midi data in case a new file was loaded
        self._parse_midi_data()

    def update(self, delta_time: float):
        """
        Update the state of all notes.

        Args:
            delta_time: Time passed since the last update in seconds
        """
        if self.paused:
            return

        # Update current time
        self.current_time += delta_time

        # Check for new notes to activate
        self._activate_new_notes()

        # Update positions of active notes
        for note in self.active_notes:
            note.update(self.current_time)

            # Check if note has reached the piano (bottom of screen)
            if note.y >= self.target_y and note.status == NoteStatus.FALLING:
                note.mark_as_missed(self.current_time)
                self.misses += 1

            # Check if note should be removed (it's no longer active)
            if not note.update(self.current_time):
                note.should_be_removed = True

        # Remove notes that should be removed
        self.active_notes = [
            note for note in self.active_notes if not note.should_be_removed
        ]

    def _activate_new_notes(self):
        """Check for new notes to activate based on the current time."""
        # Look for notes that should start falling now
        new_active_notes = []
        remaining_upcoming = []

        for note in self.note_queue:
            # If the note should start falling now
            if note.start_time <= self.current_time:
                new_active_notes.append(note)
            else:
                remaining_upcoming.append(note)

        # Add new active notes
        self.active_notes.extend(new_active_notes)
        # Update upcoming notes list
        self.note_queue = remaining_upcoming

    def handle_note_played(self, note_number: int) -> bool:
        """
        Handle a note being played by the user.

        Args:
            note_number: MIDI note number that was played

        Returns:
            True if the note was hit, False otherwise
        """
        for note in self.active_notes:
            hit_status, score = note.check_hit(note_number, self.current_time)
            if hit_status:
                if hit_status == "perfect":
                    self.perfect_hits += 1
                elif hit_status == "good":
                    self.good_hits += 1
                elif hit_status == "hit":
                    self.hits += 1
                elif hit_status == "wrong":
                    self.wrong_notes += 1
                self.score += score
                return True
        return False

    def reset(self):
        """Reset the note generator to its initial state."""
        self.active_notes = []
        self.score = 0
        self.perfect_hits = 0
        self.good_hits = 0
        self.hits = 0
        self.misses = 0
        self.wrong_notes = 0
        self.hit_notes = set()
        self.current_time = 0
        self.paused = False
        self.pause_start_time = None
        self.total_pause_time = 0
        self._parse_midi_data()  # Reload notes

    def pause(self):
        """Pause the note generator."""
        if not self.paused:
            self.paused = True
            self.pause_start_time = time.time()

    def resume(self):
        """Resume the note generator."""
        if self.paused:
            self.paused = False
            pause_duration = time.time() - self.pause_start_time
            self.total_pause_time += pause_duration
            self.start_time += pause_duration  # Adjust start time

    def is_complete(self) -> bool:
        """
        Check if all notes have been processed.

        Returns:
            True if all notes have been processed, False otherwise
        """
        return len(self.note_queue) == 0 and len(self.active_notes) == 0

    def get_visible_notes(self) -> List[Note]:
        """
        Get all currently visible notes for rendering.

        Returns:
            List of visible notes
        """
        return self.active_notes

    def get_current_stats(self) -> Dict:
        """
        Get current statistics about the note generator.

        Returns:
            Dictionary containing statistics
        """
        return {
            "score": self.score,
            "perfect_hits": self.perfect_hits,
            "good_hits": self.good_hits,
            "hits": self.hits,
            "misses": self.misses,
            "wrong_notes": self.wrong_notes,
            "remaining_notes": len(self.note_queue) + len(self.active_notes),
            "is_complete": self.is_complete(),
        }
