import os
import json
import tkinter as tk
from tkinter import simpledialog, messagebox
import tempfile
from tkinter import filedialog
import reader_looper

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
    if fi.endswith('.json'):
        with open(fi, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                for video_id, value in data.items():
                    if "captions" in value:
                        captions = value["captions"]
                        for i, caption in enumerate(captions):
                            if any(term in caption["text"] for term in primary_terms):
                                if additional_terms:
                                    for offset in range(-5, 6):
                                        if offset == 0:
                                            continue
                                        idx = i + offset
                                        if 0 <= idx < len(captions):
                                            text = captions[idx]["text"]
                                            if any(term in text for term in additional_terms):
                                                url = f"https://www.youtube.com/watch?v={video_id}&t={captions[idx]['start']}s"
                                                results.append({
                                                    "file": fi,
                                                    "primary_term": caption["text"],
                                                    "additional_term": text,
                                                    "line": idx,
                                                    "url": url
                                                })
                                else:
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
        for result in results:
            html_content += f"<li><strong>File:</strong> {result['file']}<br>"
            html_content += f"<strong>Primary:</strong> {result['primary_term']}<br>"
            html_content += f"<strong>Additional:</strong> {result['additional_term']} (Line {result['line']})<br>"
            html_content += f"<strong>URL:</strong> <a href='{result['url']}'>{result['url']}</a><br><br></li>"
            links.append(result['url'])
        html_content += "</ul></body></html>"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as temp_file:
            temp_file.write(html_content)
            temp_file_path = temp_file.name
        os.system(temp_file_path)
        return links
    else:
        messagebox.showinfo("Search Results", "No matches found.")


def main():
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
            "Additional Terms", "Enter additional search terms (comma-separated):")
        additional_terms = [term.strip() for term in additional_terms_str.split(
            ',')] if additional_terms_str else []

        # Search and display results
        results = search_json_files(f, primary_terms, additional_terms)

        # Modified part: Write results to an HTML file and then open it
        html_file_name = "search_results.html"
        links = display_results_in_browser(results)
    else:
        messagebox.showwarning("Input Error", "Primary terms are required.")
        
    reader_looper.download(links)
    # Close the Tkinter root object
    root.destroy()

if __name__ == "__main__":
    main()