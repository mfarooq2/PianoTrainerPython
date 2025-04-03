import os
import time
import threading
from typing import Dict, Optional, List, Tuple
import pygame.mixer


class SoundEngine:
    """
    Sound engine for piano note playback.
    Handles loading and playing piano samples, with real-time playback
    capabilities for MIDI events.
    """
    
    def __init__(self, samples_dir: str, channels: int = 32, buffer: int = 512):
        """
        Initialize the sound engine with specified audio parameters.
        
        Args:
            samples_dir: Directory containing piano samples
            channels: Number of mixer channels to allocate
            buffer: Audio buffer size (smaller = less latency but potential audio issues)
        """
        # Initialize pygame mixer
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=buffer)
        pygame.mixer.set_num_channels(channels)
        
        self.samples_dir = samples_dir
        self.samples: Dict[int, pygame.mixer.Sound] = {}
        self.active_notes: Dict[int, Tuple[pygame.mixer.Channel, float]] = {}
        self.master_volume = 1.0
        self.release_time = 0.1  # Time in seconds for note release
        
        # Load samples
        self._load_samples()
    
    def _load_samples(self) -> None:
        """Load all piano samples from the samples directory."""
        if not os.path.exists(self.samples_dir):
            raise FileNotFoundError(f"Sample directory not found: {self.samples_dir}")
        
        print(f"Loading piano samples from {self.samples_dir}...")
        
        for filename in os.listdir(self.samples_dir):
            if filename.endswith('.wav') or filename.endswith('.mp3'):
                # Extract note information from filename
                # Assuming filenames like "piano_A4.wav" or "A4.wav"
                note_name = os.path.splitext(filename)[0]
                
                # Convert note name to MIDI note number
                midi_note = self._note_name_to_midi(note_name)
                if midi_note is not None:
                    sample_path = os.path.join(self.samples_dir, filename)
                    try:
                        self.samples[midi_note] = pygame.mixer.Sound(sample_path)
                        print(f"Loaded sample for MIDI note {midi_note}: {filename}")
                    except pygame.error as e:
                        print(f"Error loading sample {filename}: {e}")
    
    def _note_name_to_midi(self, note_name: str) -> Optional[int]:
        """
        Convert a note name (e.g., 'A4') to MIDI note number.
        Handles various filename formats.
        
        Args:
            note_name: Note name, possibly with prefix (e.g., 'piano_A4' or 'A4')
            
        Returns:
            MIDI note number or None if conversion fails
        """
        # Strip any prefix (like "piano_")
        for prefix in ["piano_", "key_", "note_"]:
            if prefix in note_name:
                note_name = note_name.split(prefix)[-1]
        
        # Handle note names like A4, C5, etc.
        if len(note_name) >= 2 and note_name[-1].isdigit():
            try:
                # Extract note and octave
                if note_name[-2] == '#':
                    note = note_name[:-2]
                    octave = int(note_name[-1])
                    is_sharp = True
                else:
                    note = note_name[:-1]
                    octave = int(note_name[-1])
                    is_sharp = False
                
                # Convert to MIDI note number
                notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                if is_sharp:
                    note = note + '#'
                
                if note in notes:
                    note_index = notes.index(note)
                    # MIDI note 60 is middle C (C4)
                    return 12 * (octave + 1) + note_index
            except (ValueError, IndexError):
                pass
                
        # Handle direct MIDI number in filename
        try:
            # If the filename directly contains the MIDI note number
            return int(note_name)
        except ValueError:
            return None
    
    def play_note(self, midi_note: int, velocity: int = 127, duration: Optional[float] = None) -> None:
        """
        Play a piano note with the specified MIDI note number and velocity.
        
        Args:
            midi_note: MIDI note number (0-127)
            velocity: MIDI velocity (0-127)
            duration: Note duration in seconds, None for indefinite
        """
        if midi_note not in self.samples:
            print(f"Warning: No sample for MIDI note {midi_note}")
            return
        
        # Convert velocity (0-127) to volume (0.0-1.0)
        volume = min(1.0, (velocity / 127) * self.master_volume)
        
        # Get a free channel
        channel = pygame.mixer.find_channel(True)  # True = force if no channels available
        if not channel:
            print("Warning: No available channels for playback")
            return
            
        # Play the note
        channel.set_volume(volume)
        channel.play(self.samples[midi_note])
        
        # Store the active note with its start time
        self.active_notes[midi_note] = (channel, time.time())
        
        # If duration specified, schedule note release
        if duration is not None:
            threading.Timer(duration, self.stop_note, args=[midi_note]).start()
    
    def stop_note(self, midi_note: int) -> None:
        """
        Stop a currently playing note with a short release time.
        
        Args:
            midi_note: MIDI note number to stop
        """
        if midi_note in self.active_notes:
            channel, _ = self.active_notes[midi_note]
            
            # Fade out for smooth release
            channel.fadeout(int(self.release_time * 1000))
            
            # Remove from active notes
            del self.active_notes[midi_note]
    
    def stop_all_notes(self) -> None:
        """Stop all currently playing notes."""
        # Make a copy of keys since we're modifying the dictionary
        active_notes = list(self.active_notes.keys())
        for midi_note in active_notes:
            self.stop_note(midi_note)
    
    def set_master_volume(self, volume: float) -> None:
        """
        Set the master volume for all notes.
        
        Args:
            volume: Volume level between 0.0 and 1.0
        """
        self.master_volume = max(0.0, min(1.0, volume))
        
        # Update all currently playing notes
        for midi_note, (channel, _) in self.active_notes.items():
            channel.set_volume(self.master_volume)
    
    def process_midi_event(self, event_type: str, note: int, velocity: int = 127, 
                           duration: Optional[float] = None) -> None:
        """
        Process a MIDI event.
        
        Args:
            event_type: Type of event ('note_on' or 'note_off')
            note: MIDI note number
            velocity: Note velocity (0-127)
            duration: Duration in seconds (only used for note_on events)
        """
        if event_type == 'note_on' and velocity > 0:
            self.play_note(note, velocity, duration)
        elif event_type == 'note_off' or (event_type == 'note_on' and velocity == 0):
            self.stop_note(note)
    
    def set_release_time(self, release_time: float) -> None:
        """
        Set the release time for note stopping.
        
        Args:
            release_time: Release time in seconds
        """
        self.release_time = max(0.01, release_time)
    
    def cleanup(self) -> None:
        """Clean up resources and stop pygame mixer."""
        self.stop_all_notes()
        pygame.mixer.quit()


# Example usage
if __name__ == "__main__":
    import time
    
    # Example of how to use the sound engine
    samples_dir = "../media/samples"
    engine = SoundEngine(samples_dir)
    
    # Play a C major chord
    engine.play_note(60)  # C4
    engine.play_note(64)  # E4
    engine.play_note(67)  # G4
    
    # Wait for a moment
    time.sleep(2)
    
    # Play a scale with different velocities
    for note in range(60, 73):
        velocity = 50 + (note - 60) * 5  # Increasing velocity
        engine.play_note(note, velocity, 0.5)
        time.sleep(0.2)
    
    # Wait for the last note to finish
    time.sleep(1)
    
    # Clean up
    engine.cleanup()

