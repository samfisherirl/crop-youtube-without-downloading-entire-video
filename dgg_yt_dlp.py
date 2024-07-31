import re
import tkinter as tk
from tkinter import ttk
import subprocess
from pathlib import Path
from datetime import datetime
import os
import tkinter as tk
from tkinter import ttk

time_str = datetime.now().strftime("%H%M%S")
yt_dlp = Path.cwd() / "yt-dlp.exe"


def extract_youtube_base_url(input_url):
    # Regex to match the main part of YouTube URLs (both short and long versions)
    regex = r"(https://(www\.)?youtube\.com/watch\?v=|https://youtu\.be/)([^&?/\s]+)"
    # Search for matches using the regex
    match = re.search(regex, input_url)
    # If a match is found, reconstruct the base YouTube URL
    if match:
        video_id = match.group(3)
        base_url_long = f"https://www.youtube.com/watch?v={video_id}"
        base_url_short = f"https://youtu.be/{video_id}"
        # Return both possibilities, or select one depending on your need
        return base_url_long, base_url_short
    return None


def find_words_in_captions(words, json_data):
    result = {word: [] for word in words}
    for video_id, content in json_data.items():
        for caption in content["captions"]:
            for word in words:
                if word in caption["text"]:
                    result[word].append(
                        {"videoID": video_id, "start": caption["start"]})
    return result


class PartialClipDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.clipboard_content = ""
        self.monitoring_clipboard = False
        self._create_widgets()
        self.start_clipboard_monitoring()

    def _apply_theme(self):
        """Apply the dark theme from an external file if available."""
        try:
            theme = Path.cwd() / 'theme' / "azure.tcl"
            self.root.tk.call("source", str(theme))
            self.root.tk.call("set_theme", "dark")
        except Exception as e:
            print('No theme file found. Using default theme.')

    def _create_widgets(self):
        """Create and layout the widgets in the main application window."""
        self.root.title("DGG YouTube Partial Clip Downloader")
        # Define the font
        font = ("Arial", 16)

        # Use a frame to organize widgets
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Configure the grid column to allow the Entry widgets to expand
        self.main_frame.columnconfigure(1, weight=1)

        # URL Entry
        ttk.Label(self.main_frame, text="YouTube URL:", font=font).grid(
            column=0, row=0, sticky="w")
        self.url_entry = ttk.Entry(self.main_frame, width=50,
                                   font=font)
        self.url_entry.grid(column=1, row=0, sticky="ew", padx=5, pady=5)

        # Start Time Entry
        ttk.Label(self.main_frame, text="Start Time (in seconds):", font=font).grid(
            column=0, row=1, sticky="w")
        self.start_time_entry = ttk.Entry(self.main_frame, width=50, font=font)
        self.start_time_entry.grid(
            column=1, row=1, sticky="ew", padx=5, pady=5)

        # End Time Entry
        ttk.Label(self.main_frame, text="End Time (in seconds):", font=font).grid(
            column=0, row=2, sticky="w")
        self.end_time_entry = ttk.Entry(self.main_frame, width=50, font=font)
        self.end_time_entry.grid(column=1, row=2, sticky="ew", padx=5, pady=5)

        ttk.Label(self.main_frame, text="Keyframe Mode:", font=font).grid(
            column=0, row=3, sticky="w")
        self.force_keyframes_var = tk.StringVar(value="fast")
        self.keyframe_mode_dropdown = ttk.Combobox(
            self.main_frame, textvariable=self.force_keyframes_var, values=["fast/approx", "slow/perfect"], font=font, state="readonly")
        self.keyframe_mode_dropdown.grid(
            column=1, row=3, sticky="ew", padx=5, pady=5)

        # Download Button
        # This button will ideally trigger the download process for the video clip.
        # The 'command' parameter is expected to link to a method that handles the download.
        # Here you should replace 'self.download_video' with the actual method name once implemented.
        self.download_button = ttk.Button(
            self.main_frame, text="Download Clip", command=self.download_video)
        self.download_button.grid(
            column=1, row=4, sticky="ew", padx=5, pady=25)
        # Message Label
        # This label can be used to display messages to the user, such as download progress or errors.
        self.message_label = ttk.Label(self.main_frame, text="")
        self.message_label.grid(column=0, row=5, columnspan=2, sticky="ew")

    def _get_force_keyframes(self):
        return self.force_keyframes_var.get()

    def _add_right_click_menu(self):
        """Adds right-click context menu with 'Paste' functionality to entry widgets."""
        self.rc_menu = tk.Menu(self.root, tearoff=0)
        self.rc_menu.add_command(label="Paste", command=self._paste)

        self.url_entry.bind("<Button-3>", self._show_rc_menu)
        self.start_time_entry.bind("<Button-3>", self._show_rc_menu)
        self.end_time_entry.bind("<Button-3>", self._show_rc_menu)

    def _show_rc_menu(self, event):
        """Shows right-click menu."""
        try:
            self.rc_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.rc_menu.grab_release()

    def _paste(self):
        """Pastes content from clipboard to focused widget."""
        try:
            self.root.focus_get().insert(tk.INSERT, self.root.clipboard_get())
        except tk.TclError:
            pass

    def extract_timestamp_from_url(self, url):
        if "t=" in url:
            timestamp = url.split("t=")[-1]
            if "s" in timestamp:
                timestamp = timestamp.replace("s", "")
            # Handling the case where there might be other parameters after 't'
            timestamp = timestamp.split(
                "&")[0] if "&" in timestamp else timestamp
            return timestamp
        return ""

    def start_clipboard_monitoring(self):
        """Starts monitoring the clipboard in a non-blocking way."""
        if not self.monitoring_clipboard:
            self.monitoring_clipboard = True
            try:
                self.monitor_clipboard_for_youtube_url()
            except Exception as e:
                print(
                    f"\n\nError monitoring clipboard: {e}\n\nthis is NOT an issue, just a warning.")

    def monitor_clipboard_for_youtube_url(self):
        """Monitors the clipboard for YouTube URLs and sets it in the URL entry if detected."""
        clipboard_content = self.root.clipboard_get()
        if "youtube.com" in clipboard_content and clipboard_content != self.clipboard_content:
            self.clipboard_content = clipboard_content
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, clipboard_content)
            timestamp = self.extract_timestamp_from_url(clipboard_content)
            if timestamp:
                self.start_time_entry.delete(0, tk.END)
                self.start_time_entry.insert(0, timestamp)
                endtime = 0
                try:
                    startime = int(timestamp) - 30
                    endtime = int(timestamp) + 30
                except Exception as e:
                    print(f'Error converting timestamp:{e}')
                self.start_time_entry.delete(0, tk.END)
                self.start_time_entry.insert(0, startime)
                self.end_time_entry.delete(0, tk.END)
                self.end_time_entry.insert(0, endtime)
        self.root.after(1000, self.monitor_clipboard_for_youtube_url)

    def download_video(self):
        youtube_url = self.url_entry.get()
        start_time = self.start_time_entry.get()
        end_time = self.end_time_entry.get()

        if "&" in youtube_url:
            youtube_url = youtube_url.split("&")[0]
        # Ensure time string is in a proper format if added to the filename
        time_str = f"{start_time}-{end_time}"
        filename = f"{youtube_url.split('=')[-1]}_{time_str}.mp4".strip()

        # Path to the yt-dlp executable
        # Assume yt-dlp is in PATH. Adjust if needed.
        yt_dlp = Path.cwd() / "yt-dlp.exe"
        if start_time.strip() == "":
            start_time = 0
        if end_time.strip() == "":
            end_time = 0
        # Construct the command for yt-dlp
        if 'fast' in self._get_force_keyframes():
            fcf = ""
        else:
            fcf = "--force-keyframes-at-cuts"
        command = [
            str(yt_dlp),
            "--downloader", "ffmpeg", "-N", '12',
            "-o", f"%(title)s-{time_str}.%(ext)s",
            "--download-sections", f"*{start_time}-{end_time}",
            f'--verbose',
            '--extractor-args',  "youtube:player_client=web",
            # "--downloader-args", f"ffmpeg_i:-ss {start_time} -to {end_time}",
            youtube_url
        ]
        if fcf != '':
            command.append(f'{fcf}')
        backup_command = [
            str(yt_dlp), youtube_url,
            "--downloader", "ffmpeg", "-N", '36',
            "-o", f"{time_str}.%(ext)s",
            "--external-downloader-args", f"ffmpeg:-http_persistent 0 -ss {start_time} -to {end_time}"
        ]
        print(f"Executing command:{command}")
        try:
            # Attempt to download the video clip
            subprocess.run([str(yt_dlp), '-U'])
            subprocess.run(command, check=True)
            self.message_label.config(
                text="Download Successful!", foreground="lime green")
        except subprocess.CalledProcessError:
            self.message_label.config(
                text="Download Failed! Check the details and try again.", foreground="red")
            subprocess.run(backup_command, check=True)


def main():
    """Main function to create the tkinter GUI application."""
    root = tk.Tk()

    app = PartialClipDownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
