import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip


def split_video(video_path, timestamps, workingdir):
    if not os.path.exists(workingdir):
        os.makedirs(workingdir)

    clips = []
    for i, (start, end) in enumerate(timestamps, 1):
        output_clip_path = os.path.join(workingdir, f"clip_{i}.mp4")
        ffmpeg_extract_subclip(video_path, start, end,
                                targetname=output_clip_path)
        clips.append(output_clip_path)
    return clips


def combine_clips(clips, output_path):
    video_clips = [VideoFileClip(clip) for clip in clips]
    final_clip = concatenate_videoclips(video_clips, method="compose", padding=0.1)
    final_clip.write_videofile(output_path)


# Example usage
timestamps = [(10, 20), (40, 60), (90, 120)]  # Start and end times in seconds
video_path = r"C:\Users\dower\Videos\2024-07-20_04-18-47.mp4"
workingdir = os.path.dirname(video_path)

clips = split_video(video_path, timestamps, workingdir)
combine_clips(clips, "combined_video.mp4")
