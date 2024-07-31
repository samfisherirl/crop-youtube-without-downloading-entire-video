import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import sv_ttk
import html2text
import re
from datetime import datetime
import subprocess
from concurrent.futures import ProcessPoolExecutor

MAX_PER_VIDEO = 2
LENGTH = 10

class aLog:
    def __init__(self, root):
        self.root = root
        self.root.title("Ryle_Kittenhouse")

        # Set dark theme
        sv_ttk.set_theme("dark")

        # Edit Field 1
        self.edit_field1_label = ttk.Label(root, text="Edit Field 1:")
        self.edit_field1_label.grid(row=0, column=0, padx=10, pady=5)
        self.edit_field1 = ttk.Entry(root)
        self.edit_field1.grid(row=0, column=1, padx=10, pady=5)

        # Edit Field 2
        self.edit_field2_label = ttk.Label(root, text="Edit Field 2:")
        self.edit_field2_label.grid(row=1, column=0, padx=10, pady=5)
        self.edit_field2 = ttk.Entry(root)
        self.edit_field2.grid(row=1, column=1, padx=10, pady=5)

        # Dropdown Menu
        self.dropdown_label = ttk.Label(root, text="Dropdown Menu:")
        self.dropdown_label.grid(row=2, column=0, padx=10, pady=5)
        self.dropdown_var = tk.StringVar()
        self.dropdown_menu = ttk.Combobox(root, textvariable=self.dropdown_var)
        self.dropdown_menu['values'] = ('Option 1', 'Option 2')
        self.dropdown_menu.grid(row=2, column=1, padx=10, pady=5)

        # Number Input
        self.number_input_label = ttk.Label(root, text="Number Input:")
        self.number_input_label.grid(row=3, column=0, padx=10, pady=5)
        self.number_input = ttk.Entry(root)
        self.number_input.grid(row=3, column=1, padx=10, pady=5)

        # Buttons
        self.button1 = ttk.Button(
            root, text="Button 1", command=self.button1_action)
        self.button1.grid(row=4, column=0, padx=10, pady=10)

        self.button2 = ttk.Button(
            root, text="Button 2", command=self.button2_action)
        self.button2.grid(row=4, column=1, padx=10, pady=10)

        self.button3 = ttk.Button(
            root, text="Button 3", command=self.button3_action)
        self.button3.grid(row=4, column=2, padx=10, pady=10)

    # Methods for Button Actions
    def button1_action(self):
        global yt_dlp
        file = self.select_file()
        primary_terms_str = self.edit_field1.get()
        additional_terms_str = self.edit_field2.get()
        primary_terms = [term.strip() for term in primary_terms_str.split(',')]
        additional_terms = [term.strip() for term in additional_terms_str.split(
            ',') if additional_terms_str] or []
        f = self.extract_timestamp_from_url(self.dropdown_var.get())
        self.execute_task(f)
        results = self.search_directory_for_json_files(
            f, primary_terms, additional_terms)
        self.display_results_in_browser(results)

    def button2_action(self):
        # Placeholder button action
        pass

    def button3_action(self):
        # Placeholder button action
        pass

    # Method for opening file dialog to select a file
    def select_file(self):
        root = tk.Tk()
        root.withdraw()  # Hide the main Tkinter window
        root.attributes('-topmost', True)  # Make the file dialog always on top
        # Set the working directory as the start path for the file dialog
        start_path = os.getcwd()
        file_path = filedialog.askopenfilename(initialdir=start_path)
        if file_path:
            print(f"Selected file: {file_path}")
        else:
            print("No file selected.")
        root.destroy()  # Destroy the root Tk instance
        return file_path

    # Additional required functions from the second script
    def extract_timestamp_from_url(self, url):
        if "t=" in url:
            timestamp = url.split("t=")[-1]
            if "s" in timestamp:
                timestamp = timestamp.replace("s", "")
            timestamp = timestamp.split(
                "&")[0] if "&" in timestamp else timestamp
            return timestamp
        return False

    def execute_task(self, link):
        timestamp = self.extract_timestamp_from_url(link)
        self.execute_command(float(timestamp), link)
        return True

    def download(self, links):
        with ProcessPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(self.execute_task, link)
                       for link in links]
        for future in futures:
            success = future.result()
            print(f"Task completed: {success}")

    def search_directory_for_json_files(self, directory, primary_terms, additional_terms=None):
        all_results = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    results = self.search_json_files(
                        file_path, primary_terms, additional_terms)
                    all_results.extend(results)
        return all_results

    def execute_command(self, start_time, youtube_url):
        end_time = start_time + LENGTH
        start_time = start_time - LENGTH
        command = [
            str(yt_dlp),
            "--downloader", "ffmpeg", "-N", '24',
            "-o", f"%(title)s-{start_time}.%(ext)s",
            "--download-sections", f"*{start_time}-{end_time}",
            '--verbose', '--force-keyframes-at-cuts',
            '--extractor-args', "youtube:player_client=web",
            youtube_url
        ]
        try:
            subprocess.run([str(yt_dlp), '-U'])
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError:
            print('\n\n\nerror')

    def html_to_text(self, html_content):
        h = html2text.HTML2Text()
        h.ignore_links = True
        return h.handle(html_content)

    def find_links(self, document):
        return re.findall(r'https?://\S+', document)

    def search_json_files(self, fi, primary_terms, additional_terms=None):
        # Placeholder
        pass

    def display_results_in_browser(self, results):
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


if __name__ == "__main__":
    root = tk.Tk()
    app = aLog(root)
    root.mainloop()
