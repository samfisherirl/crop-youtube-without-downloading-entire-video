import moviepy.editor as mp
from datetime import datetime, timedelta
import os
from moviepy.video.fx.fadein import fadein

def ms_to_timedelta(ms):
    # Converts milliseconds to timedelta
    return timedelta(milliseconds=ms)


def convert_to_avi_uncompressed(video_path):
    # Load the video
    video = mp.VideoFileClip(video_path)
    # Define the output path for the AVI file
    output_avi = "temp_uncompressed.avi"
    # Convert to AVI Uncompressed
    video.write_videofile(output_avi, codec='rawvideo',
                        ffmpeg_params=["-pix_fmt", "yuv420p"])
    # Close the video to free resources
    video.close()
    return output_avi


def convert_to_mp4_after_edit(avi_path):
    # Load the edited AVI video
    edited_video = mp.VideoFileClip(avi_path)
    # Define the final MP4 output path
    output_mp4 = "final_output.mp4"
    # Convert to MP4
    edited_video.write_videofile(output_mp4, codec='libx264')
    # Close the video to free resources
    edited_video.close()
    # Remove the temporary AVI file
    os.remove(avi_path)


def cut_video(video_path, timecodes):
    # First convert the input video to AVI uncompressed
    uncompressed_avi = convert_to_avi_uncompressed(video_path)

    # Load the uncompressed AVI video
    video = mp.VideoFileClip(uncompressed_avi)

    # Initialize a list to store the clips to concatenate
    clips = []

    # Processing each tuple of start and end time in the timecodes
    for i, (start, end) in enumerate(timecodes):
        # Convert string times to datetime.timedelta
        start_delta = datetime.strptime(
            start, "%H:%M:%S.%f") - datetime(1900, 1, 1)
        end_delta = datetime.strptime(
            end, "%H:%M:%S.%f") - datetime(1900, 1, 1)

        # Append the clip from start to end to the clips list
        clips.append(video.subclip(str(start_delta), str(end_delta)))

    # Apply crossfade of 0.1 seconds between clips using list comprehension
    faded_clips = [clips[0]] + [clip.crossfadein(0.3) for clip in clips[1:]]
    final_clip = mp.concatenate_videoclips(
        faded_clips, padding=-0.2, method="compose")

    # Write the edited clips into a temporary AVI file
    temp_output_avi = "edited_uncompressed.avi"
    final_clip.write_videofile(temp_output_avi, codec='rawvideo', ffmpeg_params=[
                               "-pix_fmt", "yuv420p"])

    # Close all resources from the first pass
    video.close()
    final_clip.close()
    for clip in clips:
        clip.close()

    # Convert the edited AVI back to MP4 and remove temporary files
    convert_to_mp4_after_edit(temp_output_avi)
    # Remove the initial uncompressed AVI
    os.remove(uncompressed_avi)
    
# Example usage
cut_video("input.mp4", [("00:00:05.000", "00:00:08.500"),
          ("00:00:09.900", "00:00:15.000"), ("00:00:19.000", "00:00:21.000")])
