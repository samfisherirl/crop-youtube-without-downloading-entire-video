import os
import json
import tkinter as tk
from tkinter import simpledialog, messagebox
import tempfile
from tkinter import filedialog
from concurrent.futures import ProcessPoolExecutor
import time
import re
import subprocess
from pathlib import Path
import html2text
from datetime import datetime
from tkinter import simpledialog
import sys 

MAX_PER_VIDEO = 2
LENGTH = 10

def show_integer_entry_dialog(message):
    global LENGTH
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window

    user_input = simpledialog.askinteger(
        "Video Length Seconds", message, initialvalue=10)

    root.destroy()  # Destroy the root Tk instance
    LENGTH = user_input
    return user_input

def show_confirmation_popup(message):
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window

    answer = messagebox.askyesno("Confirmation", message)

    root.destroy()  # Destroy the root Tk instance

    return answer


def select_file():
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window

    # Make the file dialog always on top
    root.attributes('-topmost', True)

    # Set the working directory as the start path for the file dialog
    start_path = os.getcwd()

    file_path = filedialog.askopenfilename(initialdir=start_path)
    if file_path:
        print(f"Selected file: {file_path}")
    else:
        print("No file selected.")

    # Destroy the root to prevent lingering after execution
    root.destroy()
    return file_path


def search_json_files(fi, primary_terms, additional_terms=None):
    results = []
    global LENGTH
    LENGTH = int(LENGTH/2)
    if fi.endswith('.json'):
        with open(fi, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                for video_id, value in data.items():
                    if "captions" in value:
                        captions = value["captions"]
                        for i, caption in enumerate(captions):
                            counter = 0
                            if any(term in caption["text"] for term in primary_terms if term.strip() != '' or term != False):
                                if additional_terms:
                                    for offset in range(-5, 6):
                                        breaker = False
                                        if offset == 0:
                                            continue
                                        idx = i + offset
                                        if 0 <= idx < len(captions) and breaker == False:
                                            text = captions[idx]["text"]
                                            counter += 1
                                            if any(term in text for term in additional_terms if term.strip() != '' or term != False):
                                                if counter > MAX_PER_VIDEO:
                                                    continue
                                                url = f"https://www.youtube.com/watch?v={video_id}&t={captions[idx]['start']}s"
                                                results.append({
                                                    "file": fi,
                                                    "primary_term": caption["text"],
                                                    "additional_term": text,
                                                    "line": idx,
                                                    "url": url
                                                })
                                            breaker=True
                                else:
                                    if counter > MAX_PER_VIDEO:
                                        continue
                                    counter += 1
                                    url = f"https://www.youtube.com/watch?v={video_id}&t={caption['start']}s"
                                    results.append({
                                        "file": fi,
                                        "primary_term": caption["text"],
                                        "additional_term": 'null',
                                        "line": i,
                                        "url": url
                                    })
            except Exception as e:
                print(f"Error reading {fi}: {e}")
    return results


# Get the path to the directory containing the executable
exe_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))

# Specify the path to yt-dlp.exe
yt_dlp = os.path.join(exe_dir, "yt-dlp.exe")

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


def create_date_folder():
    global exe_dir
    current_datetime = datetime.now()
    folder_name = current_datetime.strftime("%Y-%m-%d_%H-%M-%S") 
    folder_path = os.path.join(exe_dir, folder_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        return folder_path

def execute_command(start_time, youtube_url):
    global yt_dlp
    end_time=start_time + LENGTH
    start_time=start_time - LENGTH
    
    folder_path=create_date_folder()
    folder = os.path.dirname(folder_path)
    output_path=os.path.join(
        folder, f"%(title)s-{start_time}.mp4")

    command=[
        str(yt_dlp),
        "--downloader", "ffmpeg", "-N", '24',
        "-o", output_path,
        "--download-sections", f"*{start_time}-{end_time}",
        '--merge-output-format', 'mp4',
        '--verbose', '--force-keyframes-at-cuts',
        '--extractor-args', "youtube:player_client=web",
        youtube_url
    ]
    try:
        subprocess.run([str(yt_dlp), '-U'])
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        print('\n\n\nerror')

# def execute_command(start_time, youtube_url):
#     global yt_dlp
#     end_time = start_time + LENGTH
#     start_time = start_time - LENGTH
#     command = [
#         str(yt_dlp),
#         "--downloader", "ffmpeg", "-N", '24',
#         "-o", f"%(title)s-{start_time}.%(ext)s",
#         "--download-sections", f"*{start_time}-{end_time}",
#         '--verbose', '--force-keyframes-at-cuts',
#         '--extractor-args', "youtube:player_client=web",
#         youtube_url
#     ]

def html_to_text(html_content):
    h = html2text.HTML2Text()
    h.ignore_links = True
    return h.handle(html_content)

def find_links(document):
    return re.findall(r'https?://\S+', document)
    
def execute_task(link):
    timestamp = extract_timestamp_from_url(link)
    execute_command(float(timestamp), link)
    # Return some indication of success/failure, optional
    return True

def download(links):
    """
    for link in links:
        timestamp = extract_timestamp_from_url(link)
        execute_command(float(timestamp), link)
    """
    with ProcessPoolExecutor(max_workers=2) as executor:
    # Using submit and as_completed for more granular control, map can also be used
        futures = [executor.submit(execute_task, link) for link in links]

    # Optionally: Retrieve and process the results asynchronously
    for future in futures:
        # result method will wait for the individual process to complete
        success = future.result()
        # Process your success/failure here
        print(f"Task completed: {success}")

def search_directory_for_json_files(directory, primary_terms, additional_terms=None):
    all_results = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                results = search_json_files(
                    file_path, primary_terms, additional_terms)
                all_results.extend(results)
    return all_results

# Function to write results to an HTML file and open with default browser
def show_simple_messagebox(title, message):
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window
    messagebox.showinfo(title, message)
    root.destroy()


def display_results_in_browser(results):
    links = []
    if results:
        html_content = "<html><head><title>Search Results</title></head><body>"
        html_content += "<h1>Search Results</h1><ul>"
        last_prime = ''
        last_additional = ''
        for result in results:
            if last_prime != "" and last_prime == result['primary_term'] or last_additional != 'null' and last_additional == result['additional_term']:
                continue
            html_content += f"<li><strong>File:</strong> {result['file']}<br>"
            html_content += f"<strong>Primary:</strong> {result['primary_term']}<br>"
            html_content += f"<strong>Additional:</strong> {result['additional_term']} (Line {result['line']})<br>"
            html_content += f"<strong>URL:</strong> <a href='{result['url']}'>{result['url']}</a><br><br></li>"
            links.append(result['url'])
            last_prime = result['primary_term']
            last_additional = result['additional_term']
        html_content += "</ul></body></html>"
        dt = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        temp_file_path = f'search{dt}.html'
        with open(temp_file_path, mode="w", encoding="utf-8") as temp_file:
            temp_file.write(html_content)
        os.system(temp_file_path)
        return links
    else:
        messagebox.showinfo("Search Results", "No matches found.")


def search_cut_compile():
    # Create the Tkinter root object and set it to be always on top
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    # Prompt user for primary term and additional terms
    show_simple_messagebox('select', 'select a transcript')
    # Prompt user for primary term and additional terms
    f = select_file()
    primary_terms_str = simpledialog.askstring(
        "Primary Terms", "Enter the primary search terms (comma-separated):")
    if primary_terms_str:
        primary_terms = [term.strip() for term in primary_terms_str.split(',')]
        additional_terms_str = simpledialog.askstring(
            "Additional Terms", "Secondary Terms (around the primary search term, optional) \nEnter additional search terms (comma-separated):")
        additional_terms = [term.strip() for term in additional_terms_str.split(
            ',')] if additional_terms_str else []

        # Search and display results
        results = search_json_files(f, primary_terms, additional_terms)
        
        # Modified part: Write results to an HTML file and then open it
        html_file_name = "search_results.html"
        links = display_results_in_browser(results)
    else:
        messagebox.showwarning("Input Error", "Primary terms are required.")
    if show_confirmation_popup('Download videos from transcript?'):
        show_integer_entry_dialog("How many seconds before and after the timestamp should the video be?")
        for link in links:
            execute_task(link)
    # Close the Tkinter root object
    root.destroy()

if __name__ == "__main__":
    print(str(Path.cwd()))
    search_cut_compile()