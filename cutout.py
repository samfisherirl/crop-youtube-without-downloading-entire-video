import re
import subprocess
from datetime import datetime, timedelta
import os
import tkinter as tk
from tkinter import filedialog
from concurrent.futures import ThreadPoolExecutor

def select_srt_file():
    root = tk.Tk()
    root.withdraw()  # Hide the tkinter root window
    file_path = filedialog.askopenfilename(filetypes=[("SRT files", "*.srt")])
    if file_path:
        with open(file_path, 'r') as file:
            srt_content = file.read()
        return srt_content
    return None


def cut_video_speaking_parts(input_video, subtitle_text, output_folder):
    output_path = os.path.join(output_folder, 'output.mp4')
    speaking_periods = compute_speaking_periods(subtitle_text)
    # Initialize the filter complex list to prepare cutting and combining command
    filter_complex = []
    # Loop through speaking periods to generate video and audio filters for each period
    for i, (start, end) in enumerate(speaking_periods):
        # Add video trim filter for current speaking period
        filter_complex.append(
            f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}]; ")
        # Add audio trim filter for current speaking period
        filter_complex.append(
            f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}]; ")

    # Generate strings to reference all video and audio tracks for concatenation
    video_tracks = ''.join([f"[v{i}]" for i in range(len(speaking_periods))])
    audio_tracks = ''.join([f"[a{i}]" for i in range(len(speaking_periods))])
    
    # Complete the filter_complex string by adding a concat filter at the end
    filter_complex_string = ''.join(
        filter_complex) + f"{video_tracks}{audio_tracks}concat=n={len(speaking_periods)}:v=1:a=1[outv][outa]"
    
    # Construct the ffmpeg command with the filter_complex string
    command = [
        'ffmpeg',
        '-i', input_video,  # Input video file path
        # The constructed filter_complex command
        '-filter_complex', filter_complex_string,
        # Map the output of filter_complex to output file
        '-map', '[outv]', '-map', '[outa]',
        output_path  # Output file path
    ]
    
    # Execute the ffmpeg command
    subprocess.run(command)

    
def select_video_file():
    root = tk.Tk()
    root.withdraw()  # Hide the tkinter root window
    file_path = filestart_prompt = filedialog.askopenfilename(
        filetypes=[("Video files", "*.mp4 *.mov")])
    return file_path
def parse_time(s):
    return datetime.strptime(s, '%H:%M:%S,%f')


def compute_speaking_periods(subtitle_text):
    timestamps = re.findall(
        r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})', subtitle_text)
    periods = []
    for start, end in timestamps:
        periods.append((start.replace(',', '.'), end.replace(',', '.')))
    return periods

def combine_videos(video_paths, final_output):
    filelist_path = os.path.splitext(final_output)[0] + '_filelist.txt'
    with open(filelist_path, 'w') as filelist:
        for path in video_paths:
            filelist.write(f"file '{path}'\n")

    command = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', filelist_path,
        '-fflags', '+genpts',
        '-preset', 'veryfast',
        '-y',
        final_output
    ]
    subprocess.run(command)
    os.remove(filelist_path)  # Clean up the filelist
    for path in video_paths:
        os.remove(path)
    print(f"Combined videos saved as {final_output}")



    
subtitle_text = """
14
00:00:01,980 --> 00:00:03,160
<font color="#f9a100">Before</font>

15
00:00:09,200 --> 00:00:11,300
<font color="#f9a100">you</font> think,

16
00:00:13,300 --> 00:00:23,460
you <font color="#f9a100">think,</font>

17
00:00:23,520 --> 00:00:33,660
<font color="#f9a100">this</font> guy is
"""
# select_srt_file()

cut_video_speaking_parts(
    select_video_file(), subtitle_text, '')
