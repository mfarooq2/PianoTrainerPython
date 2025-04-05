import unittest
import os
from midi_processing.midi_loader import MidiLoader


class TestMidiLoader(unittest.TestCase):
    def setUp(self):
        # Create a MidiLoader instance
        self.loader = MidiLoader()
        # Define path to test midi file (will be created manually later)
        self.test_midi_path = "midi_processing/tests/test_midi.mid"

    def test_get_tempo_at_time(self):
        # This test will verify the _get_tempo_at_time method
        # We will need to create a test MIDI file with known tempo changes
        # and assert that the method returns the correct tempo at different times.
        self.assertTrue(
            self.loader.load_midi_file(self.test_midi_path),
            "Failed to load test MIDI file",
        )

        # Assertions based on the assumed test MIDI file
        self.assertEqual(
            self.loader._get_tempo_at_time(0.0), 500000
        )  # Initial tempo: 120 BPM
        self.assertEqual(
            self.loader._get_tempo_at_time(0.99), 500000
        )  # Still initial tempo
        self.assertEqual(
            self.loader._get_tempo_at_time(1.0), 400000
        )  # Tempo changed to 150 BPM
        self.assertEqual(self.loader._get_tempo_at_time(2.49), 400000)  # Still 150 BPM
        self.assertEqual(
            self.loader._get_tempo_at_time(2.5), 600000
        )  # Tempo changed to 100 BPM
        self.assertEqual(self.loader._get_tempo_at_time(3.0), 600000)  # Still 100 BPM

    def test_extract_chords(self):
        # This test will verify the extract_chords method
        self.assertTrue(
            self.loader.load_midi_file(self.test_midi_path),
            "Failed to load test MIDI file",
        )

        # Expected chords (assuming specific content in test_midi.mid)
        expected_chords = [
            [60, 64, 67],  # C major (C4, E4, G4)
            [67, 71, 74],  # G major (G4, B4, D5)
        ]

        # Extract chords with a 50ms tolerance
        extracted_chords = self.loader.extract_chords(max_start_diff=0.05)

        # Assert that at least one chord is extracted
        self.assertGreater(len(extracted_chords), 0, "No chords extracted")

        # Analyze the extracted chords
        for i, chord in enumerate(extracted_chords):
            # Assert that each chord has at least 3 notes
            self.assertGreaterEqual(
                len(chord), 3, f"Chord {i+1} has fewer than 3 notes"
            )

            # Assert that the maximum start time difference within the chord is within the tolerance
            if len(chord) > 1:
                start_times = [note.start_time for note in chord]
                max_diff = max(start_times) - min(start_times)
                self.assertLessEqual(
                    max_diff,
                    0.05,
                    f"Chord {i+1} has notes with start times differing by more than 50ms",
                )


if __name__ == "__main__":
    unittest.main()
