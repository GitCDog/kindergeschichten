#!/usr/bin/env python3
"""Update seconds for archived audio files (stories 1-5)."""

import logging
from pathlib import Path
from input_reader import InputReader

class ArchivedAudioUpdater:
    """Update audio durations for archived files."""

    def __init__(self):
        self.logger = self._setup_logging()
        self.archive_dir = Path("output/1_insta_post_X")

    def _setup_logging(self):
        """Setup logging."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        return logging.getLogger(__name__)

    def get_audio_duration(self, audio_file: Path) -> int:
        """Get audio duration from MP3 file."""
        try:
            with open(audio_file, 'rb') as f:
                f.seek(0)
                frames = 0
                sample_rate = 0

                while True:
                    header = f.read(4)
                    if len(header) < 4:
                        break

                    if (header[0] == 0xFF) and ((header[1] & 0xE0) == 0xE0):
                        version = (header[1] >> 3) & 0x3
                        layer = (header[1] >> 1) & 0x3
                        bitrate_idx = (header[2] >> 4) & 0xF
                        sample_rate_idx = (header[2] >> 2) & 0x3
                        padding = (header[2] >> 1) & 0x1

                        if version == 3 and layer == 1:
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
                    duration = (frames * 1152) // sample_rate
                    return int(duration)

                # Fallback: estimate from file size
                file_size_mb = audio_file.stat().st_size / (1024 * 1024)
                estimated_duration = int(file_size_mb * 8 / 0.128)
                return estimated_duration

        except Exception as e:
            self.logger.warning(f"Could not get duration for {audio_file.name}: {e}")
            return 0

    def update_archived_durations(self):
        """Update durations for archived audio files (stories 1-5)."""
        if not self.archive_dir.exists():
            self.logger.error(f"Archive directory not found: {self.archive_dir}")
            return

        audio_files = sorted(self.archive_dir.glob("*.mp3"))

        if not audio_files:
            self.logger.info("No audio files found in archive")
            return

        self.logger.info(f"Found {len(audio_files)} archived audio files")
        self.logger.info("=" * 60)

        input_reader = InputReader("input/0_input_all_stories.txt")
        updated_count = 0

        for audio_file in audio_files:
            # Extract story number: {numbering}_{story_name}.mp3
            stem = audio_file.stem
            parts = stem.split("_", 1)

            try:
                numbering = int(parts[0])
                duration = self.get_audio_duration(audio_file)

                if duration > 0:
                    stories = input_reader.read_stories()
                    story_info = next((s for s in stories if int(s["numbering"]) == numbering), None)

                    if story_info:
                        story_name = story_info["story_name"]
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
        self.logger.info(f"[+] Updated {updated_count} archived stories")


def main():
    """Main entry point."""
    updater = ArchivedAudioUpdater()
    updater.update_archived_durations()


if __name__ == "__main__":
    main()
