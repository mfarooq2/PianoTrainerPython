import random
import pygame
from typing import List, Dict, Tuple, Optional, Callable, Set

# Import from other modules
from enhanced_piano_trainer.midi_processing.midi_loader import MidiLoader
from enhanced_piano_trainer.ui.piano_view import PianoView
from enhanced_piano_trainer.audio.sound_engine import SoundEngine


class PracticeMode:
    """Base class for all practice modes"""
    
    def __init__(self, piano_view: PianoView, sound_engine: SoundEngine):
        self.piano_view = piano_view
        self.sound_engine = sound_engine
        self.is_active = False
        self.difficulty = 1  # 1-5 scale
        
    def start(self):
        """Start the practice session"""
        self.is_active = True
        
    def stop(self):
        """Stop the practice session"""
        self.is_active = False
        
    def set_difficulty(self, level: int):
        """Set the difficulty level (1-5)"""
        if 1 <= level <= 5:
            self.difficulty = level
            
    def update(self, events: List[pygame.event.Event], midi_inputs: List = None) -> None:
        """
        Update the practice mode based on user input
        
        Args:
            events: List of pygame events
            midi_inputs: Optional list of MIDI input events
        """
        pass
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw practice mode specific elements on the surface
        
        Args:
            surface: Pygame surface to draw on
        """
        pass
    
    def get_feedback(self) -> Dict:
        """
        Get feedback on the current practice session
        
        Returns:
            Dictionary containing feedback metrics
        """
        return {"score": 0, "accuracy": 0, "time": 0}


class NoteIdentificationPractice(PracticeMode):
    """Practice mode for identifying notes on the keyboard"""
    
    def __init__(self, piano_view: PianoView, sound_engine: SoundEngine):
        super().__init__(piano_view, sound_engine)
        self.current_note = None
        self.correct_answers = 0
        self.total_attempts = 0
        self.time_remaining = 60  # 60 seconds practice session
        self.last_time = 0
        self.font = pygame.font.Font(None, 36)
        self.instructions = "Press the highlighted key on your MIDI keyboard"
        self.feedback_message = ""
        
    def start(self):
        super().start()
        self.correct_answers = 0
        self.total_attempts = 0
        self.time_remaining = 60
        self.last_time = pygame.time.get_ticks()
        self.select_random_note()
        
    def select_random_note(self):
        """Select a random note for the user to identify"""
        # Range changes based on difficulty level
        min_note = 60 - (self.difficulty * 5)  # C4 (middle C) as baseline
        max_note = 72  (self.difficulty * 5)  # C5  difficulty range
        
        # Ensure we're within MIDI range (0-127)
        min_note = max(21, min_note)  # A0
        max_note = min(108, max_note)  # C8
        
        self.current_note = random.randint(min_note, max_note)
        # Highlight the note on the piano view
        self.piano_view.highlight_key(self.current_note, (255, 215, 0))  # Gold color
        # Play the note
        self.sound_engine.play_note(self.current_note, velocity=80)
        
    def update(self, events: List[pygame.event.Event], midi_inputs: List = None) -> None:
        """Update the practice session based on time and user input"""
        # Update timer
        current_time = pygame.time.get_ticks()
        elapsed = (current_time - self.last_time) / 1000.0  # convert to seconds
        self.last_time = current_time
        
        if self.is_active:
            self.time_remaining -= elapsed
            
            # Process MIDI inputs if available
            if midi_inputs:
                for note, velocity, _ in midi_inputs:
                    if velocity > 0:  # Note on event
                        self.check_note(note)
            
            # Check for time expiration
            if self.time_remaining <= 0:
                self.is_active = False
                self.feedback_message = f"Time's up! Score: {self.correct_answers}/{self.total_attempts}"
        
        # Check for keyboard input (for testing without MIDI keyboard)
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not self.is_active:
                    self.start()
                # Map some keyboard keys to piano notes for testing
                elif self.is_active and event.key in range(pygame.K_a, pygame.K_z + 1):
                    test_note = self.current_note + (event.key - pygame.K_a - 12)
                    self.check_note(test_note)
    
    def check_note(self, played_note: int):
        """Check if the played note matches the current note"""
        self.total_attempts = 1
        
        if played_note == self.current_note:
            self.correct_answers = 1
            self.feedback_message = "Correct!"
            # Wait a moment before selecting a new note
            pygame.time.delay(500)
            self.select_random_note()
        else:
            self.feedback_message = f"Incorrect! You played {self.get_note_name(played_note)}, should be {self.get_note_name(self.current_note)}"
            # Play the correct note again
            self.sound_engine.play_note(self.current_note, velocity=80)
    
    def get_note_name(self, midi_note: int) -> str:
        """Convert MIDI note number to note name (C4, D#3, etc.)"""
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi_note // 12) - 1
        note_idx = midi_note % 12
        return f"{notes[note_idx]}{octave}"
    
    def draw(self, surface: pygame.Surface) -> None:
        """Draw practice-specific UI elements"""
        # Instructions
        instruction_text = self.font.render(self.instructions, True, (255, 255, 255))
        surface.blit(instruction_text, (20, 20))

        # Feedback
        if self.feedback_message:
            feedback_text = self.font.render(self.feedback_message, True, (255, 215, 0))
            surface.blit(feedback_text, (20, 60))

        # Score
        score_text = self.font.render(f"Score: {self.correct_answers}/{self.total_attempts}", True, (255, 255, 255))
        score_rect = score_text.get_rect(topright=(surface.get_width() - 20, 20))
        surface.blit(score_text, score_rect)

        # Progress (Time Remaining)
        progress_text = self.font.render(f"Time: {int(self.time_remaining)}s", True, (255, 255, 255))
        progress_rect = progress_text.get_rect(topright=(surface.get_width() - 20, 60))
        surface.blit(progress_text, progress_rect)
    
    def get_feedback(self) -> Dict:
        """Get session feedback metrics"""
        accuracy = (self.correct_answers / self.total_attempts * 100) if self.total_attempts > 0 else 0
        return {
            "score": self.correct_answers,
            "attempts": self.total_attempts,
            "accuracy": accuracy,
            "time": 60 - self.time_remaining
        }


class ScalePractice(PracticeMode):
    """Practice mode for learning and playing scales"""
    
    def __init__(self, piano_view: PianoView, sound_engine: SoundEngine):
        super().__init__(piano_view, sound_engine)
        self.scales = {
            'C Major': [60, 62, 64, 65, 67, 69, 71, 72],  # C Major scale starting at C4
            'G Major': [55, 57, 59, 60, 62, 64, 66, 67],  # G Major scale
            'F Major': [53, 55, 57, 58, 60, 62, 64, 65],  # F Major scale
            'A Minor': [57, 59, 60, 62, 64, 65, 67, 69],  # A Minor scale
            'D Minor': [50, 52, 53, 55, 57, 58, 60, 62],  # D Minor scale
            'E Minor': [52, 54, 55, 57, 59, 60, 62, 64],  # E Minor scale
        }
        
        # Add more advanced scales at higher difficulty levels
        self.advanced_scales = {
            'C Harmonic Minor': [60, 62, 63, 65, 67, 68, 71, 72],
            'D Melodic Minor': [50, 52, 53, 55, 57, 59, 61, 62],
            'G Harmonic Minor': [55, 57, 58, 60, 62, 63, 66, 67],
            'C Diminished': [60, 61, 63, 64, 66, 67, 69, 70],
            'C Whole Tone': [60, 62, 64, 66, 68, 70, 72],
        }
        
        self.current_scale_name = "C Major"
        self.current_scale = self.scales[self.current_scale_name]
        self.current_position = 0
        self.direction = 1  # 1 for ascending, -1 for descending
        self.expecting_note = self.current_scale[0]
        self.font = pygame.font.Font(None, 36)
        self.instructions = "Play the highlighted scale notes in order"
        self.feedback_message = ""
        
    def start(self):
        super().start()
        self.select_scale()
        
    def select_scale(self):
        """Select a scale based on current difficulty level"""
        available_scales = list(self.scales.keys())
        
        # Add advanced scales at higher difficulty levels
        if self.difficulty >= 3:
            available_scales.extend(list(self.advanced_scales.keys())[:self.difficulty-2])
            
        self.current_scale_name = random.choice(available_scales)
        
        if self.current_scale_name in self.scales:
            self.current_scale = self.scales[self.current_scale_name]
        else:
            self.current_scale = self.advanced_scales[self.current_scale_name]
            
        self.current_position = 0
        self.direction = 1
        self.expecting_note = self.current_scale[0]
        
        # Highlight the first note
        self.piano_view.reset_highlights()
        self.piano_view.highlight_key(self.expecting_note, (0, 255, 0))
        
        # Highlight the entire scale with a different color
        for note in self.current_scale:
            if note != self.expecting_note:
                self.piano_view.highlight_key(note, (100, 100, 255), priority=1)
    
    def draw(self, surface: pygame.Surface) -> None:
        """Draw practice-specific UI elements"""
        # Instructions
        instruction_text = self.font.render(self.instructions, True, (255, 255, 255))
        surface.blit(instruction_text, (20, 20))

        # Feedback
        if self.feedback_message:
            feedback_text = self.font.render(self.feedback_message, True, (255, 215, 0))
            surface.blit(feedback_text, (20, 60))

        # Score
        score_text = self.font.render(f"Score: 0", True, (255, 255, 255))  # Initialize score to 0
        score_rect = score_text.get_rect(topright=(surface.get_width() - 20, 20))
        surface.blit(score_text, score_rect)

        # Current scale name
        scale_name_text = self.font.render(f"Scale: {self.current_scale_name}", True, (255, 255, 255))
        scale_name_rect = scale_name_text.get_rect(topright=(surface.get_width() - 20, 60))
        surface.blit(scale_name_text, scale_name_rect)
    
    def get_feedback(self) -> Dict:
        """Get session feedback metrics"""
        accuracy = 0.0
        return {
            "score": 0,
            "accuracy": accuracy,
        }

class ChordPractice(PracticeMode):
    """Practice mode for learning and playing chords from MIDI files."""

    def __init__(self, piano_view: PianoView, sound_engine: SoundEngine):
        super().__init__(piano_view, sound_engine)
        self.midi_loader = MidiLoader()
        self.available_chords: List[List[int]] = []  # List of chords (list of note numbers)
        self.current_chord: List[int] = []
        self.font = pygame.font.Font(None, 36)
        self.instructions = "Play the highlighted chord"
        self.feedback_message = ""
        self.correct_chords = 0
        self.total_attempts = 0

    def start(self):
        super().start()
        self.correct_chords = 0
        self.total_attempts = 0

        # Load a default MIDI file for chord extraction (replace with actual file path if available)
        midi_file_path = "resources/test_midi.mid"
        if not self.midi_loader.load_midi_file(midi_file_path):
            self.feedback_message = "Error loading MIDI file for chords."
            self.is_active = False
            return

        # Extract chords (assuming extract_chords now returns a list of lists of note numbers)
        self.available_chords = [[note.note for note in chord] for chord in self.midi_loader.extract_chords()]

        if not self.available_chords:
            self.feedback_message = "No chords found in the MIDI file."
            self.is_active = False
            return

        self.select_random_chord()

    def select_random_chord(self):
        """Select a random chord from the available chords and highlight it on the piano."""
        self.current_chord = random.choice(self.available_chords)
        self.piano_view.reset_highlights()
        for note in self.current_chord:
            self.piano_view.highlight_key(note, (0, 255, 255))  # Cyan for chords

    def update(self, events: List[pygame.event.Event], midi_inputs: List = None) -> None:
        """Update the practice session based on user input."""
        if not self.is_active:
            return

        if midi_inputs:
            # Check for note on events and collect played notes
            played_notes = {note for note, velocity, _ in midi_inputs if velocity > 0}

            # Check if the played notes match the current chord
            if set(self.current_chord) == played_notes:
                self.correct_chords = 1
                self.total_attempts = 1
                self.feedback_message = "Correct chord!"
                self.select_random_chord()
            elif played_notes:
                self.total_attempts = 1
                self.feedback_message = "Incorrect chord."
                self.provide_chord_feedback(played_notes)

    def provide_chord_feedback(self, played_notes: Set[int]):
        """Provides specific feedback about played chord (missing or wrong notes)"""
        missing_notes = set(self.current_chord) - played_notes
        wrong_notes = played_notes - set(self.current_chord)

        feedback_parts = []
        if missing_notes:
            missing_note_names = ", ".join([self.midi_loader.get_note_name(note) for note in missing_notes])
            feedback_parts.append(f"Missing notes: {missing_note_names}")
        if wrong_notes:
            wrong_note_names = ", ".join([self.midi_loader.get_note_name(note) for note in wrong_notes])
            feedback_parts.append(f"Wrong notes: {wrong_note_names}")

        if feedback_parts:
            self.feedback_message = ", ".join(feedback_parts)
        else:
            self.feedback_message = "Incorrect chord."  # Fallback if no specific feedback

    def draw(self, surface: pygame.Surface) -> None:
        """Draw practice-specific UI elements."""
        # Draw instructions
        instruction_text = self.font.render(self.instructions, True, (255, 255, 255))
        surface.blit(instruction_text, (20, 20))

        # Draw current chord
        chord_name = ", ".join([self.midi_loader.get_note_name(note) for note in self.current_chord])
        chord_text = self.font.render(f"Chord: {chord_name}", True, (0, 255, 255))
        surface.blit(chord_text, (20, 60))

        # Draw feedback
        if self.feedback_message:
            feedback_text = self.font.render(self.feedback_message, True, (255, 215, 0))
            surface.blit(feedback_text, (20, 100))

    def get_feedback(self) -> Dict:
        """Get session feedback metrics."""
        accuracy = (self.correct_chords / self.total_attempts * 100) if self.total_attempts > 0 else 0
        return {
            "score": self.correct_chords,
            "attempts": self.total_attempts,
            "accuracy": accuracy,
        }

    def draw(self, surface: pygame.Surface) -> None:
        """Draw practice-specific UI elements."""
        # Instructions
        instruction_text = self.font.render(self.instructions, True, (255, 255, 255))
        surface.blit(instruction_text, (20, 20))

        # Feedback
        if self.feedback_message:
            feedback_text = self.font.render(self.feedback_message, True, (255, 215, 0))
            surface.blit(feedback_text, (20, 100))

        # Score
        score_text = self.font.render(f"Score: {self.correct_chords}/{self.total_attempts}", True, (255, 255, 255))
        score_rect = score_text.get_rect(topright=(surface.get_width() - 20, 20))
        surface.blit(score_text, score_rect)
