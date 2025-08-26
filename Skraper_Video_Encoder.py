import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import sys
import subprocess
import threading
import tempfile

# --- Helper function to find ffmpeg ---
def get_ffmpeg_path():
    """
    Determines the correct path to ffmpeg executable.
    If bundled by PyInstaller, it looks in the temporary _MEIPASS folder.
    Otherwise, it assumes ffmpeg is in the system's PATH.
    """
    if getattr(sys, 'frozen', False):
        # The application is frozen (e.g., packaged by PyInstaller)
        return os.path.join(sys._MEIPASS, 'ffmpeg.exe')
    else:
        # The application is running as a normal .py script
        return 'ffmpeg'

# --- Core Application Class ---
class VideoConverterApp:
    def __init__(self, root):
        """
        Initialize the main application window and its widgets.
        """
        self.root = root
        self.root.title("Skraper Video Encoder")
        self.root.geometry("850x950")
        self.root.configure(bg="#2E2E2E")

        # --- State Variables ---
        self.directory_path = tk.StringVar()
        self.video_size = tk.StringVar(value="640x480")
        self.include_sound = tk.BooleanVar(value=True)
        self.video_length = tk.StringVar(value="20")
        self.output_option = tk.StringVar(value="trimmed") # 'trimmed' or 'overwrite'

        # --- UI Styling ---
        style = {
            "bg": "#2E2E2E",
            "fg": "#FFFFFF",
            "font": ("Arial", 10),
            "btn_bg": "#4A4A4A",
            "btn_fg": "#FFFFFF",
            "entry_bg": "#3C3C3C",
            "frame_bg": "#383838",
            "label_font": ("Arial", 11, "bold")
        }

        # --- Main Frame ---
        main_frame = tk.Frame(root, bg=style["bg"], padx=20, pady=20)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # --- 1. Directory Selection ---
        dir_frame = tk.LabelFrame(main_frame, text="1. Select Video Folder", bg=style["frame_bg"], fg=style["fg"], padx=10, pady=10, font=style["label_font"])
        dir_frame.pack(fill=tk.X, pady=(0, 15))

        dir_entry = tk.Entry(dir_frame, textvariable=self.directory_path, state='readonly', width=60, readonlybackground="#E0E0E0", fg="#1E1E1E")
        dir_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=4, padx=(0, 10))

        browse_button = tk.Button(dir_frame, text="Browse...", command=self.select_directory, bg=style["btn_bg"], fg=style["btn_fg"])
        browse_button.pack(side=tk.RIGHT)

        # --- 2. Conversion Options ---
        options_frame = tk.LabelFrame(main_frame, text="2. Conversion Options", bg=style["frame_bg"], fg=style["fg"], padx=10, pady=10, font=style["label_font"])
        options_frame.pack(fill=tk.X, pady=(0, 15))

        # Video Size
        size_frame = tk.Frame(options_frame, bg=style["frame_bg"])
        size_frame.pack(fill=tk.X, pady=5)
        tk.Label(size_frame, text="Video Size:", bg=style["frame_bg"], fg=style["fg"], font=style["font"]).pack(side=tk.LEFT, padx=(0, 10))
        tk.Radiobutton(size_frame, text="640x480", variable=self.video_size, value="640x480", bg=style["frame_bg"], fg=style["fg"], selectcolor="#555").pack(side=tk.LEFT)
        tk.Radiobutton(size_frame, text="320x240", variable=self.video_size, value="320x240", bg=style["frame_bg"], fg=style["fg"], selectcolor="#555").pack(side=tk.LEFT, padx=10)

        # Sound Option
        sound_frame = tk.Frame(options_frame, bg=style["frame_bg"])
        sound_frame.pack(fill=tk.X, pady=5)
        tk.Checkbutton(sound_frame, text="Include Sound", variable=self.include_sound, bg=style["frame_bg"], fg=style["fg"], selectcolor="#555").pack(side=tk.LEFT)

        # Video Length
        length_frame = tk.Frame(options_frame, bg=style["frame_bg"])
        length_frame.pack(fill=tk.X, pady=5)
        tk.Label(length_frame, text="Video Length (seconds):", bg=style["frame_bg"], fg=style["fg"], font=style["font"]).pack(side=tk.LEFT, padx=(0, 10))
        tk.Entry(length_frame, textvariable=self.video_length, width=10, bg=style["entry_bg"], fg=style["fg"]).pack(side=tk.LEFT)

        # --- 3. Output Options ---
        output_frame = tk.LabelFrame(main_frame, text="3. Output", bg=style["frame_bg"], fg=style["fg"], padx=10, pady=10, font=style["label_font"])
        output_frame.pack(fill=tk.X, pady=(0, 15))
        tk.Radiobutton(output_frame, text="Save to 'trimmed' sub-folder", variable=self.output_option, value="trimmed", bg=style["frame_bg"], fg=style["fg"], selectcolor="#555").pack(anchor=tk.W)
        tk.Radiobutton(output_frame, text="Overwrite original files", variable=self.output_option, value="overwrite", bg=style["frame_bg"], fg=style["fg"], selectcolor="#555").pack(anchor=tk.W)

        # --- 4. Start Conversion ---
        self.start_button = tk.Button(main_frame, text="Start Conversion", command=self.start_conversion_thread, bg="#007ACC", fg=style["btn_fg"], font=("Arial", 12, "bold"), pady=10)
        self.start_button.pack(fill=tk.X, pady=(5, 15))

        # --- 5. Log Output ---
        log_frame = tk.LabelFrame(main_frame, text="Log", bg=style["frame_bg"], fg=style["fg"], padx=10, pady=10, font=style["label_font"])
        log_frame.pack(expand=True, fill=tk.BOTH)
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, bg=style["entry_bg"], fg=style["fg"], height=10, state='disabled')
        self.log_area.pack(expand=True, fill=tk.BOTH)

    def select_directory(self):
        """
        Opens a dialog to select a directory and updates the entry field.
        """
        path = filedialog.askdirectory()
        if path:
            self.directory_path.set(path)
            self.log_message(f"Selected directory: {path}")

    def log_message(self, message):
        """
        Appends a message to the log area in a thread-safe way.
        """
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')
        self.root.update_idletasks()

    def start_conversion_thread(self):
        """
        Starts the conversion process in a new thread to keep the GUI responsive.
        """
        self.start_button.config(state=tk.DISABLED, text="Processing...")
        conversion_thread = threading.Thread(target=self.run_conversion)
        conversion_thread.daemon = True
        conversion_thread.start()

    def run_conversion(self):
        """
        The main logic for finding and converting video files.
        This method is run in a separate thread.
        """
        try:
            input_dir = self.directory_path.get()
            if not input_dir:
                messagebox.showerror("Error", "Please select a directory first.")
                return

            try:
                duration = int(self.video_length.get())
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number for video length.")
                return

            video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
            files_to_convert = [f for f in os.listdir(input_dir) if os.path.splitext(f)[1].lower() in video_extensions]

            if not files_to_convert:
                self.log_message("No video files found in the selected directory.")
                messagebox.showinfo("Info", "No video files found to convert.")
                return

            self.log_message(f"Found {len(files_to_convert)} video file(s). Starting conversion...")
            is_overwrite = self.output_option.get() == 'overwrite'
            ffmpeg_executable = get_ffmpeg_path() # Get the correct path to ffmpeg

            output_dir = input_dir
            if not is_overwrite:
                output_dir = os.path.join(input_dir, 'trimmed')
                os.makedirs(output_dir, exist_ok=True)
                self.log_message(f"Output will be saved to: {output_dir}")

            for i, filename in enumerate(files_to_convert):
                input_path = os.path.join(input_dir, filename)
                output_path = ""
                temp_output_path = ""

                if is_overwrite:
                    file_name, file_ext = os.path.splitext(filename)
                    temp_file = tempfile.NamedTemporaryFile(delete=False, dir=input_dir, prefix=f"{file_name}_temp_", suffix=file_ext)
                    temp_output_path = temp_file.name
                    temp_file.close()
                    output_path = temp_output_path
                else:
                    output_path = os.path.join(output_dir, filename)

                self.log_message(f"\n({i+1}/{len(files_to_convert)}) Processing: {filename}")

                command = [
                    ffmpeg_executable, # Use the path we found
                    '-y',
                    '-i', input_path,
                    '-r', '30',
                    '-s', self.video_size.get(),
                    '-ss', '0',
                    '-to', str(duration)
                ]

                if not self.include_sound.get():
                    command.append('-an')

                command.append(output_path)
                self.log_message(f"Executing command: {' '.join(command)}")

                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo)
                stdout, stderr = process.communicate()

                if process.returncode == 0:
                    self.log_message(f"SUCCESS: Converted {filename}")
                    if is_overwrite:
                        try:
                            os.remove(input_path)
                            os.rename(temp_output_path, input_path)
                            self.log_message(f"Replaced original file: {filename}")
                        except OSError as e:
                            self.log_message(f"ERROR replacing file {filename}: {e}")
                            if os.path.exists(temp_output_path):
                                os.remove(temp_output_path)
                else:
                    self.log_message(f"ERROR converting {filename}:")
                    self.log_message(stderr)
                    if is_overwrite and os.path.exists(temp_output_path):
                        os.remove(temp_output_path)

            self.log_message("\n--- All conversions finished! ---")
            messagebox.showinfo("Complete", "All video conversions are complete.")

        except FileNotFoundError:
             self.log_message("ERROR: ffmpeg.exe not found.")
             self.log_message("Please make sure ffmpeg.exe is in the same directory, in your system's PATH, or bundled with the application.")
             messagebox.showerror("ffmpeg Not Found", "ffmpeg.exe could not be found.")
        except Exception as e:
            self.log_message(f"An unexpected error occurred: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        finally:
            self.root.after(0, self.enable_start_button)
            
    def enable_start_button(self):
        """
        Safely re-enables the start button from the main GUI thread.
        """
        self.start_button.config(state=tk.NORMAL, text="Start Conversion")

# --- Main execution block ---
if __name__ == "__main__":
    root = tk.Tk()
    app = VideoConverterApp(root)
    root.mainloop()
