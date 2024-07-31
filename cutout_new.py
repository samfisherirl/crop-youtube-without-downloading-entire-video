import numpy as np
import os
import moviepy.editor as mp
import librosa
import subprocess
from vad import EnergyVAD
import subprocess
import moviepy.editor as mp
import numpy as np
import soundfile as sf
from moviepy.editor import concatenate_videoclips, AudioFileClip, VideoFileClip, concatenate_audioclips
import subprocess


import os
import subprocess


def check_and_delete(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


class VideoConverter:
    def __init__(self, input_path):
        self.input_path = input_path

    def convert_to_avi(self):
        output_path = self.input_path.replace(
            '.mp4', '.avi').replace('.mov', '.avi')
        subprocess.run(
            ['ffmpeg', '-i', self.input_path, output_path], check=True)
        return output_path

    def split_video(self, input_path):
        chunk_duration = self.get_video_duration(input_path) // 3
        output_paths = []
        for i in range(3):
            start_time = i * chunk_duration
            output_path = f"chunk_{i}.avi"
            subprocess.run(['ffmpeg', '-i', input_path, '-ss', str(start_time),
                           '-t', str(chunk_duration), output_path], check=True)
            output_paths.append(output_path)
        return output_paths

    def combine_videos(self, input_paths, output_path):
        with open('files.txt', 'w') as f:
            for path in input_paths:
                f.write(f"file '{path}'\n")
        subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0',
                       '-i', 'files.txt', '-c', 'copy', output_path, '-y'], check=True)
        os.remove('files.txt')

    def get_video_duration(self, input_path):
        result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of',
                                'default=noprint_wrappers=1:nokey=1', input_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
        return int(float(result.stdout))

    def convert_to_seconds(self, time_str):
        parts = time_str.split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        else:
            return int(parts[0])

    def cut_video_into_parts(self, source, input_parts):
        if not os.path.exists(source):
            print(f"Source file {source} does not exist.")
            return
        output_parts = []
        for i, part in enumerate(input_parts):
            output_path = f"part{i}.avi"
            check_and_delete(output_path)
            try:
                start_time, duration = self.convert_to_seconds(
                    part[0]), self.convert_to_seconds(part[1])
                subprocess.run(['ffmpeg', '-i', source, '-ss', str(start_time),
                               '-t', str(duration), '-c', 'copy', output_path, '-y'], check=True)
                output_parts.append(output_path)
            except subprocess.CalledProcessError as e:
                print(f"Error cutting video part {i}: {e}")
        return output_parts

    def avi_to_mp4(self, input_path, output_path):
        subprocess.run(['ffmpeg', '-i', input_path, output_path], check=True)

    def cleanup(self, paths):
        for path in paths:
            os.remove(path)

    def final_process(self):
        avi_file = self.convert_to_avi()
        chunks = self.split_video(avi_file)
        combined_avi = "combined.avi"
        self.combine_videos(chunks, combined_avi)
        final_mp4 = "final.mp4"
        self.avi_to_mp4(combined_avi, final_mp4)
        self.cleanup([avi_file] + chunks + [combined_avi])


converter = VideoConverter("input.mp4")
converter.final_process()
