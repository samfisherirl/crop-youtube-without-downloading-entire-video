
def load_audio_with_librosa(audio_path, sr=None):
    # Add sr to specify sample rate
    audio, sr = librosa.load(audio_path, sr=sr)
    return audio, sr


def load_video_with_moviepy(video_path):
    video = VideoFileClip(video_path)
    fps = video.fps
    video.close()
    return video, fps


def create_relative_folder(path):
    dir_name = os.path.splitext(path)[0] + "_splits"
    os.makedirs(dir_name, exist_ok=True)
    return dir_name


def convert_video_to_audio(video_file, sample_rate=44100):
    fold = os.path.dirname(video_file)
    audio_out = os.path.join(fold, 'audio.wav')
    cmd = [
        "ffmpeg",
        '-y',
        "-i", video_file,
        "-vn",  # No video.
        "-acodec", "pcm_s16le",  # Set codec to PCM s16 le
        "-ar", str(sample_rate),  # Audio sample rate
        "-ac", "2",  # Stereo
        audio_out
    ]
    subprocess.run(cmd, check=True)
    return audio_out


def split_and_convert(video_path, audio_path, seconds_split):
    video = load_video_with_moviepy(video_path)
    # Pass None to maintain original sample rate
    audio, sr = load_audio_with_librosa(audio_path, None)

    folder_path = create_relative_folder(video_path)

    video_durations = np.arange(0, video.duration, seconds_split)
    audio_durations = np.arange(0, len(audio)/sr, seconds_split)

    video_paths = []
    audio_paths = []

    for i, (v_start, a_start) in enumerate(zip(video_durations[:-1], audio_durations[:-1])):
        v_end = min(v_start + seconds_split, video.duration)
        a_end = min(a_start + seconds_split, len(audio)/sr)

        video_clip = video.subclip(v_start, v_end)
        video_filename = os.path.join(folder_path, f"video_{i}.mp4")
        video_paths.append(video_filename)
        video_clip.write_videofile(video_filename, audio_codec='aac')

        audio_clip = audio[int(a_start*sr):int(a_end*sr)]

        sf.write(os.path.join(
            folder_path, f"audio_{i}.wav"), audio_clip, sr)
        audio_paths.append(os.path.join(
            folder_path, f"audio_{i}.wav"))
    return video_paths, audio_paths, sr


def analyze_and_filter_slices(audio_paths, video_paths, sample_rate=16000):
    for i, (audio_path, video_path) in enumerate(zip(audio_paths, video_paths)):
        audio, sr = librosa.load(audio_path, sr=sample_rate)

        vad = EnergyVAD(sample_rate=sample_rate)
        if not np.any(vad(audio)):
            os.remove(audio_path)  # Remove audio slice
            os.remove(video_path)  # Remove corresponding video slice
            audio_paths.pop(i)  # Remove from audio_paths list
            video_paths.pop(i)  # Remove from video_paths list
    return audio_paths, video_paths


def concatenate_and_apply_fade(video_paths, output_path, audio_splits):
    clips = []
    for video_path, audio_path in zip(video_paths, audio_splits):
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(audio_path)

        # Ensure the audio clip is the same duration as the video
        if audio_clip.duration > video_clip.duration:
            audio_clip = audio_clip.subclip(0, video_clip.duration)
        else:
            padding_duration = video_clip.duration - audio_clip.duration
            padding = AudioFileClip.silence(duration=padding_duration)
            audio_clip = concatenate_audioclips([audio_clip, padding])

        # Define fade durations
        fade_in_duration = 0.05  # seconds
        fade_out_duration = 0.05  # seconds

        # Apply fade in and fade out effect to audio
        final_audio = audio_clip.audio_fadein(
            fade_in_duration).audio_fadeout(fade_out_duration)

        # Set audio of the video to the processed audio
        final_video_clip = video_clip.set_audio(final_audio)
        clips.append(final_video_clip)

    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
    print('finished, cleaning now')
    for video_path in video_paths:
        try:
            os.remove(video_path)
        except Exception as e:
            print(f'{e} dont worry\n\ncontinuingg')
    for video_path in audio_splits:
        try:
            os.remove(video_path)
        except Exception as e:
            print(f'{e} dont worry\n\ncontinuingg')


video_path = r'C:\Users\dower\Videos\2024-07-20_11-36-27.mp4'
seconds_split = 0.3
audio_path = convert_video_to_audio(video_path)
video_splits, audio_splits, sr = split_and_convert(
    video_path, audio_path, seconds_split)
audio_splits, video_splits = analyze_and_filter_slices(
    audio_splits, video_splits, sr)
concatenate_and_apply_fade(video_splits, 'output.mp4', audio_splits)
