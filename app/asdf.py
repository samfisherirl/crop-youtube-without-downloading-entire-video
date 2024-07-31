import os
import subprocess
import numpy as np
from moviepy.editor import VideoFileClip
from vad import EnergyVAD
import soundfile as sf


def check_and_delete(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


class VideoConverter:
    def __init__(self, input_path, temp_dir='temp'):
        self.input_path = input_path
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)

    def get_video_duration(self, input_path):
        result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                                'format=duration', '-of',
                                'default=noprint_wrappers=1:nokey=1', input_path],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return int(float(result.stdout))

    def split_video_into_tenths(self):
        video_duration = self.get_video_duration(self.input_path)
        chunk_duration = video_duration // 10
        chunks = []
        for i in range(10):
            start_time = i * chunk_duration
            output_path = os.path.join(self.temp_dir, f"chunk_{i}.mp4")
            check_and_delete(output_path)
            subprocess.run(['ffmpeg', '-i', self.input_path, '-ss', str(start_time),
                            '-t', str(chunk_duration), '-c', 'copy', output_path])
            chunks.append(output_path)
        return chunks

    def split_chunk_into_sections(self, chunk_path, section_duration_ms=40):
        chunk_duration = self.get_video_duration(chunk_path)
        section_duration = section_duration_ms / 1000  # Convert ms to seconds
        num_sections = int(chunk_duration // section_duration)
        sections = []
        for i in range(num_sections):
            start_time = i * section_duration
            video_output_path = os.path.join(
                self.temp_dir, f"section_{i}_{os.path.basename(chunk_path)}")
            check_and_delete(video_output_path)
            subprocess.run(['ffmpeg', '-i', chunk_path, '-ss', str(start_time),
                            '-t', str(section_duration), '-c', 'copy', video_output_path])
            audio_output_path = os.path.join(
                self.temp_dir, f"section_{i}_{os.path.basename(chunk_path)}.wav")
            check_and_delete(audio_output_path)
            subprocess.run(
                ['ffmpeg', '-i', video_output_path, audio_output_path])
            sections.append({"video": video_output_path,
                            "audio": audio_output_path})
        return sections

    def process_audio_with_vad(self, audio_path):
        audio, sample_rate = sf.read(audio_path)
        vad = EnergyVAD(
            sample_rate=sample_rate,
            frame_length=25,  # in milliseconds
            frame_shift=20,  # in milliseconds
            energy_threshold=0.05,  # you may need to adjust this value
            pre_emphasis=0.95,
        )
        # returns a boolean array indicating whether a frame is speech or not
        voice_activity = vad(audio)
        return any(voice_activity)  # return True if any frame is speech

    def final_process(self):
        chunks = self.split_video_into_tenths()
        all_sections = []
        for chunk in chunks:
            sections = self.split_chunk_into_sections(chunk)
            for section in sections:
                if self.process_audio_with_vad(section["audio"]):
                    all_sections.append(section)
                else:
                    check_and_delete(section["audio"])
                    check_and_delete(section["video"])
        return all_sections

    def cleanup(self):
        for root, dirs, files in os.walk(self.temp_dir):
            for file in files:
                os.remove(os.path.join(root, file))
        os.rmdir(self.temp_dir)


# Example usage
converter = VideoConverter("input.mp4")
all_section_paths = converter.final_process()
for section in all_section_paths:
    print(f"Video: {section['video']}, Audio: {section['audio']}")
