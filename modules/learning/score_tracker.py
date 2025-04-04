import time
from typing import Dict, List, Optional, Tuple
import pygame
import json
import os

class ScoreTracker:
    """
    Tracks and calculates scores for the learning mode.
    """
    def __init__(self):
        """Initialize the score tracker."""
        self.reset()
        self.high_scores_file = "scores.json"
        self.high_scores = self._load_high_scores()
        
    def reset(self):
        """Reset all scores and statistics."""
        self.notes_hit = 0
        self.notes_missed = 0
        self.total_notes = 0
        self.combo = 0
        self.max_combo = 0
        self.last_hit_time = 0
        self.score = 0
        self.start_time = time.time()
        self.end_time = None
        self.difficulty_multiplier = 1.0
        
    def note_hit(self, note_number: int, time_accuracy: float):
        """
        Register a hit note.
        
        Args:
            note_number: MIDI note number that was hit
            time_accuracy: Accuracy of the hit (0.0 to 1.0, where 1.0 is perfect)
        """
        self.notes_hit += 1
        self.total_notes += 1
        self.combo += 1
        
        # Update max combo if current combo is larger
        self.max_combo = max(self.max_combo, self.combo)
        
        # Calculate points for this hit
        accuracy_bonus = int(100 * time_accuracy)
        combo_bonus = min(self.combo * 2, 100)  # Cap combo bonus at 100
        points = 100 + accuracy_bonus + combo_bonus
        
        # Apply difficulty multiplier
        points = int(points * self.difficulty_multiplier)
        
        # Add to total score
        self.score += points
        self.last_hit_time = time.time()
        
    def note_missed(self, note_number: int):
        """
        Register a missed note.
        
        Args:
            note_number: MIDI note number that was missed
        """
        self.notes_missed += 1
        self.total_notes += 1
        self.combo = 0  # Reset combo on miss
        
    def set_difficulty(self, difficulty: str):
        """
        Set the difficulty multiplier based on the selected difficulty.
        
        Args:
            difficulty: Difficulty level (easy, medium, hard)
        """
        difficulty_map = {
            'easy': 0.8,
            'medium': 1.0,
            'hard': 1.2,
            'expert': 1.5
        }
        
        self.difficulty_multiplier = difficulty_map.get(difficulty.lower(), 1.0)
        
    def complete_session(self):
        """Mark the current session as complete and record the end time."""
        self.end_time = time.time()
        self._check_high_score()
        
    def _check_high_score(self):
        """Check if the current score is a high score and save it if so."""
        if self.score == 0:
            return
            
        song_name = "Unknown Song"  # Replace with actual song name from MIDI file if available
        
        if song_name not in self.high_scores:
            self.high_scores[song_name] = []
            
        # Add current score to list
        self.high_scores[song_name].append({
            'score': self.score,
            'accuracy': self.get_accuracy(),
            'max_combo': self.max_combo,
            'date': time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Sort scores for this song
        self.high_scores[song_name] = sorted(
            self.high_scores[song_name], 
            key=lambda x: x['score'], 
            reverse=True
        )
        
        # Keep only top 10 scores
        self.high_scores[song_name] = self.high_scores[song_name][:10]
        
        # Save high scores
        self._save_high_scores()
        
    def _load_high_scores(self) -> Dict:
        """
        Load high scores from file.
        
        Returns:
            Dictionary of high scores by song
        """
        if not os.path.exists(self.high_scores_file):
            return {}
            
        try:
            with open(self.high_scores_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
            
    def _save_high_scores(self):
        """Save high scores to file."""
        try:
            with open(self.high_scores_file, 'w') as f:
                json.dump(self.high_scores, f, indent=2)
        except IOError:
            print("Error: Could not save high scores.")
            
    def get_accuracy(self) -> float:
        """
        Calculate the current accuracy.
        
        Returns:
            Accuracy as a percentage
        """
        if self.total_notes == 0:
            return 0.0
            
        return (self.notes_hit / self.total_notes) * 100
        
    def get_session_time(self) -> float:
        """
        Get the current session time in seconds.
        
        Returns:
            Session time in seconds
        """
        if self.end_time is not None:
            return self.end_time - self.start_time
        else:
            return time.time() - self.start_time
            
    def get_performance_summary(self) -> Dict:
        """
        Get a summary of the performance for display or analysis.
        
        Returns:
            Dictionary containing summary statistics
        """
        return {
            'score': self.score,
            'accuracy': self.get_accuracy(),
            'notes_hit': self.notes_hit,
            'notes_missed': self.notes_missed,
            'max_combo': self.max_combo,
            'session_time': self.get_session_time(),
            'difficulty': self.difficulty_multiplier
        }
        
    def get_high_scores(self, song_name: str, limit: int = 5) -> List[Dict]:
        """
        Get high scores for a specific song.
        
        Args:
            song_name: Name of the song to get high scores for
            limit: Maximum number of scores to return
            
        Returns:
            List of high score dictionaries
        """
        if song_name not in self.high_scores:
            return []
            
        return self.high_scores[song_name][:limit]
