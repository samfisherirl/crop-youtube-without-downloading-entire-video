import re
import subprocess
from pathlib import Path
import html2text

yt_dlp = Path.cwd() / "yt-dlp.exe"

def extract_timestamp_from_url(url):
    if "t=" in url:
        timestamp = url.split("t=")[-1]
        if "s" in timestamp:
            timestamp = timestamp.replace("s", "")
        # Handling the case where there might be other parameters after 't'
        timestamp = timestamp.split(
            "&")[0] if "&" in timestamp else timestamp
        return timestamp
    return False


def execute_command(start_time, youtube_url):
    global yt_dlp
    end_time = start_time + 8
    start_time = start_time - 5
    command = [
        str(yt_dlp),
        "--downloader", "ffmpeg", "-N", '24',
        "-o", f"%(title)s-{start_time}.%(ext)s",
        "--download-sections", f"*{start_time}-{end_time}",
        "-N", '4', '--verbose', '--force-keyframes-at-cuts',
        '--extractor-args', "youtube:player_client=web",
        youtube_url
    ]
    try:
        subprocess.run([str(yt_dlp), '-U'])
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        print('\n\n\nerror')

def html_to_text(html_content):
    h = html2text.HTML2Text()
    h.ignore_links = True
    return h.handle(html_content)

def find_links(document):
    return re.findall(r'https?://\S+', document)


def download(links):
    for link in links:
        timestamp = extract_timestamp_from_url(link)
        execute_command(float(timestamp), link)
    
if __name__ == '__main__':
    download()