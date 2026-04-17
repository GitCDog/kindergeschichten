#!/usr/bin/env python3
"""Update seconds column for all existing audio files."""

import logging
from pathlib import Path
from input_reader import InputReader

class AudioDurationUpdater:
    """Update audio durations in input file."""

    def __init__(self):
        self.logger = self._setup_logging()
        self.output_dir = Path("output")

    def _setup_logging(self):
        """Setup logging."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        return logging.getLogger(__name__)

    def get_audio_duration(self, audio_file: Path) -> int:
        """Get audio duration in seconds from MP3 file."""
        try:
            # Parse MP3 headers manually
            with open(audio_file, 'rb') as f:
                f.seek(0)
                frames = 0
                sample_rate = 0

                while True:
                    header = f.read(4)
                    if len(header) < 4:
                        break

                    # Look for MP3 frame header (0xFFF or 0xFFE)
                    if (header[0] == 0xFF) and ((header[1] & 0xE0) == 0xE0):
                        # Valid MPEG frame
                        version = (header[1] >> 3) & 0x3
                        layer = (header[1] >> 1) & 0x3
                        bitrate_idx = (header[2] >> 4) & 0xF
                        sample_rate_idx = (header[2] >> 2) & 0x3
                        padding = (header[2] >> 1) & 0x1

                        if version == 3 and layer == 1:  # MPEG1, Layer 3
                            bitrates = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, -1]
                            sample_rates = [44100, 48000, 32000, 0]

                            if bitrate_idx > 0 and sample_rate_idx < 3:
                                bitrate = bitrates[bitrate_idx]
                                sample_rate = sample_rates[sample_rate_idx]
                                frame_size = (144000 * bitrate) // sample_rate + padding
                                frames += 1
                                f.seek(frame_size - 4, 1)
                            else:
                                break
                        else:
                            break
                    else:
                        f.seek(-3, 1)

                if frames > 0 and sample_rate > 0:
                    # Rough estimation: 1152 samples per MP3 frame at MPEG1
                    duration = (frames * 1152) // sample_rate
                    return int(duration)

            # Fallback: estimate from file size (rough)
            file_size_mb = audio_file.stat().st_size / (1024 * 1024)
            # Assume ~128 kbps average
            estimated_duration = int(file_size_mb * 8 / 0.128)
            return estimated_duration

        except Exception as e:
            self.logger.warning(f"Could not get duration for {audio_file.name}: {e}")
            return 0

    def update_all_durations(self):
        """Scan all audio files and update durations in input file."""
        # Get all audio files
        audio_files = sorted(self.output_dir.glob("*.mp3"))

        if not audio_files:
            self.logger.info("No audio files found")
            return

        self.logger.info(f"Found {len(audio_files)} audio files")
        self.logger.info("=" * 60)

        input_reader = InputReader("input/0_input_all_stories.txt")
        updated_count = 0

        for audio_file in audio_files:
            # Extract story number from filename: {numbering}_{story_name}.mp3
            # The numbering is everything before the first underscore
            stem = audio_file.stem
            parts = stem.split("_", 1)

            try:
                numbering = int(parts[0])
                # Get duration
                duration = self.get_audio_duration(audio_file)

                if duration > 0:
                    # Get story name from input file
                    stories = input_reader.read_stories()
                    story_info = next((s for s in stories if int(s["numbering"]) == numbering), None)

                    if story_info:
                        story_name = story_info["story_name"]
                        # Update seconds column
                        if input_reader.update_status(story_name, str(duration), status_field="seconds"):
                            self.logger.info(f"[+] Story #{numbering}: {duration}s")
                            updated_count += 1
                        else:
                            self.logger.warning(f"[-] Failed to update story #{numbering}")
                    else:
                        self.logger.warning(f"[-] Story #{numbering} not found in input file")
            except ValueError:
                self.logger.warning(f"[-] Invalid numbering in {audio_file.name}")
                continue

        self.logger.info("=" * 60)
        self.logger.info(f"[+] Updated {updated_count} stories with audio durations")


def main():
    """Main entry point."""
    updater = AudioDurationUpdater()
    updater.update_all_durations()


if __name__ == "__main__":
    main()
