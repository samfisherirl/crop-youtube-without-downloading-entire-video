import subprocess
import os


def check_and_delete(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


def convert_mp4_to_avi(mp4_file_path, avi_file_path):
    check_and_delete(avi_file_path)
    try:
        subprocess.run([
            "ffmpeg",
            "-i", mp4_file_path,
            "-c:v", "mpeg4",
            "-c:a", "mp3",
            avi_file_path,
            '-y',
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error converting {mp4_file_path} to avi: {e}")


def cut_video_into_parts(source, input_parts):
    if not os.path.exists(source):
        print(f"Source file {source} does not exist.")
        return
    output_parts = []
    for i, part in enumerate(input_parts):
        output_path = f"part{i}.avi"
        check_and_delete(output_path)
        try:
            start_time, duration = convert_to_seconds(
                part[0]), convert_to_seconds(part[1])
            subprocess.run([
                "ffmpeg",
                "-i", source,
                "-ss", str(start_time),
                "-t", str(duration),
                "-c", "copy",
                output_path,
                '-y',
            ], check=True)
            output_parts.append(output_path)
        except subprocess.CalledProcessError as e:
            print(f"Error cutting video part {i}: {e}")
    return output_parts


def convert_to_seconds(time_str):
    """Convert time format 'HH:MM:SS' to seconds."""
    parts = time_str.split(':')
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    else:
        return int(parts[0])


def concatenate_videos(parts, output):
    with open('concat_list.txt', 'w') as f:
        for part in parts:
            f.write(f"file '{part}'\n")
    try:
        subprocess.run([
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", "concat_list.txt",
            "-c", "copy",
            output,
            '-y',
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error concatenating videos: {e}")


def convert_to_mp4(input_file_path, output_mp4_file_path):
    check_and_delete(output_mp4_file_path)
    try:
        subprocess.run([
            "ffmpeg",
            "-i", input_file_path,
            "-c:v", "libx264",
            "-preset", "medium",
            "-c:a", "aac",
            "-strict", "-2",  # Correct value for '-strict experimental'
            output_mp4_file_path,
            '-y',
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error converting {input_file_path} to MP4: {e}")


# Usage example
try:
    convert_mp4_to_avi('input.mp4', 'temp.avi')
    # Cutting the video into 3 parts
    source_video = "temp.avi"
    cut_parts = [("00:00:01:00", "00:00:02:09"), ("00:00:03:11",
                                                "00:00:05:31"), ("00:00:09:02", "00:00:11:01")]
    parts = cut_video_into_parts(source_video, cut_parts)
    print("\n\n\n\ncut video into parts")
    # Concatenating the videos in reverse order
    concatenate_videos(parts, "output.avi")
    print("\n\n\n\nconcatenate_videos")
    print("\n\n\n\nconvert_to_mp4")
    convert_to_mp4("output.avi", "output.mp4")
    # os.remove("output.avi")
    # os.remove("temp.avi")
except Exception as e:
    print(f"An exception occurred: {e}")
