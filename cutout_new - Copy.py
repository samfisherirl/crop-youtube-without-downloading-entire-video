import os
import re
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import filedialog

# Global constant for the silence gap threshold
SILENCE_THRESHOLD_MS = 50


def select_srt_file():
    root = tk.Tk()
    root.withdraw()  # Hide the tkinter root window
    file_path = filedialog.askopenfilename(filetypes=[("SRT files", "*.srt")])
    if file_path:
        with open(file_path, 'r') as file:
            srt_content = file.read()
        return srt_content
    return None


def select_video_file():
    root = tk.Tk()
    root.withdraw()  # Hide the tkinter root window
    file_path = filedialog.askopenfilename(
        filetypes=[("Video files", "*.mp4 *.mov")])
    return file_path


def parse_time(s):
    try:
        return datetime.strptime(s, '%H:%M:%S,%f')
    except ValueError:
        return datetime.strptime(s, '%H:%M:%S.%f')

def compute_speaking_periods(subtitle_text):
    """
    Computes the speaking periods from the given subtitle text.

    Args:
        subtitle_text (str): The subtitle text containing timestamps.

    Returns:
        list: A list of tuples representing the speaking periods. Each tuple contains the start and end time in the format 'HH:MM:SS.sss'.

    """
    timestamps = re.findall(
        r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})', subtitle_text)
    periods = []
    previous_end = None

    for start, end in timestamps:
        start_time = parse_time(start)
        end_time = parse_time(end)

        if previous_end:
            # in milliseconds
            silence_duration = (
                start_time - previous_end).total_seconds() * 1000
            if silence_duration > SILENCE_THRESHOLD_MS:
                periods.append((previous_end.strftime('%H:%M:%S.%f')[
                            :-3], start_time.strftime('%H:%M:%S.%f')[:-3]))

        previous_end = end_time
    return periods




def convert_back_to_mp4(temp_avi, output_path):
    command_convert = [
        'ffmpeg',
        '-i', temp_avi,
        output_path,
        '-y'
    ]
    subprocess.run(command_convert, check=True)
    os.remove(temp_avi)



def convert_to_avi(input_video, output_folder):
    avi_output_path = os.path.join(output_folder, 'input.avi')
    command = [
        'ffmpeg',
        '-i', input_video,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        avi_output_path,
        '-y'
    ]
    try:
        subprocess.run(command, check=True)
        return avi_output_path
    except subprocess.CalledProcessError as e:
        print(f"Error converting video to AVI: {e}")
        return None
    
def cut_video_speaking_parts(input_video, subtitle_text, output_folder):
    output_path = os.path.join(output_folder, 'output.mp4')

    speaking_periods = compute_speaking_periods(subtitle_text)

    temp_files = []
    last = 0
    for i, (start, end) in enumerate(speaking_periods):
        if i == 0:
            # Cut at the first speaking start
            temp_file = os.path.join(output_folder, f'temp_{i}.mp4')
            temp_files.append(temp_file)
            command = [
                'ffmpeg', '-i', input_video, '-ss', str(start), '-to', str(end),
                '-c', 'copy', '-force_key_frames', 'expr:gte(t,n_forced*2)', temp_file, '-y'
            ]
            subprocess.run(command, check=True)
        else:
            # Check if the last end is more than before the current start
            if parse_time(end) > parse_time(speaking_periods[i-1][1]):
                # Cut the last end and create another start
                temp_file = os.path.join(output_folder, f'temp_{i}.mp4')
                temp_files.append(temp_file)
                command = [
                    'ffmpeg', '-i', input_video, '-ss', str(parse_time(speaking_periods[i-1][1])), '-to', str(parse_time(start)),
                    '-c', 'copy', '-force_key_frames', 'expr:gte(t,n_forced*2)', temp_file, '-y'
                ]
                subprocess.run(command, check=True)
            
            # Cut from the current start to end
            temp_file = os.path.join(output_folder, f'temp_{i+1}.mp4')
            temp_files.append(temp_file)
            command = [
                'ffmpeg', '-i', input_video, '-ss', str(start), '-to', str(end),
                '-c', 'copy', '-force_key_frames', 'expr:gte(t,n_forced*2)', temp_file, '-y'
            ]
            subprocess.run(command, check=True)

    concat_file = os.path.join(output_folder, 'concat_list.txt')
    with open(concat_file, 'w') as f:
        for temp_file in temp_files:
            f.write(f"file '{temp_file}'\n")

    concat_command = [
        'ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_file,
        '-c', 'copy', output_path, '-y'
    ]

    subprocess.run(concat_command, check=True)

    # Clean up temporary files
    for temp_file in temp_files:
        os.remove(temp_file)
    os.remove(concat_file)

    return output_path

# Example usage
subtitle_text = select_srt_file()
if subtitle_text:
    input_video = select_video_file()
    if input_video:
        output_folder = os.path.dirname(input_video)
        cut_video_speaking_parts(input_video, subtitle_text, output_folder)
    else:
        print("No video file selected.")
else:
    print("No subtitle file selected.")
