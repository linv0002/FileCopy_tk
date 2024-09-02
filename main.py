import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, ttk
from threading import Thread, Event


class FileCopyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Copy Utility")
        self.src_dir = ""
        self.dst_dir = ""
        self.new_files_count = 0
        self.overwritten_files_count = 0
        self.error_count = 0
        self.pause_event = Event()
        self.stop_event = Event()

        # Source and Destination selection buttons
        self.select_src_btn = tk.Button(root, text="Select Source Directory", command=self.select_source_directory)
        self.select_src_btn.grid(row=0, column=0, pady=5, padx=5, sticky=tk.W)

        self.src_dir_label = tk.Label(root, text="No source selected", anchor="w", width=60)
        self.src_dir_label.grid(row=0, column=1, pady=5, padx=5)

        self.select_dst_btn = tk.Button(root, text="Select Destination Directory",
                                        command=self.select_destination_directory)
        self.select_dst_btn.grid(row=1, column=0, pady=5, padx=5, sticky=tk.W)

        self.dst_dir_label = tk.Label(root, text="No destination selected", anchor="w", width=60)
        self.dst_dir_label.grid(row=1, column=1, pady=5, padx=5)

        # Text entry for excluding directories
        self.exclude_label = tk.Label(root, text="Exclude Directories (comma separated):")
        self.exclude_label.grid(row=2, column=0, pady=5, padx=5, sticky=tk.W)

        self.exclude_entry = tk.Entry(root, width=50)
        self.exclude_entry.grid(row=2, column=1, pady=5, padx=5)

        # Radio buttons for copy mode
        self.copy_mode = tk.StringVar(value="overwrite_all")
        self.overwrite_all_radio = tk.Radiobutton(root, text="Copy All Files (Overwrite)", variable=self.copy_mode,
                                                  value="overwrite_all")
        self.overwrite_all_radio.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5)

        self.copy_new_radio = tk.Radiobutton(root, text="Copy Only New Files", variable=self.copy_mode,
                                             value="copy_new")
        self.copy_new_radio.grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=5)

        self.copy_newer_radio = tk.Radiobutton(root, text="Copy Only Newer Files", variable=self.copy_mode,
                                               value="copy_newer")
        self.copy_newer_radio.grid(row=5, column=0, columnspan=2, sticky=tk.W, padx=5)

        # Listboxes to display copied and overwritten files
        self.copied_files_label = tk.Label(root, text="New Files Copied:")
        self.copied_files_label.grid(row=6, column=0, columnspan=2, sticky=tk.W, padx=5)
        self.copied_files_list = Listbox(root, height=5, width=80)
        self.copied_files_list.grid(row=7, column=0, columnspan=2, pady=5, padx=5)

        self.overwritten_files_label = tk.Label(root, text="Overwritten Files:")
        self.overwritten_files_label.grid(row=8, column=0, columnspan=2, sticky=tk.W, padx=5)
        self.overwritten_files_list = Listbox(root, height=5, width=80)
        self.overwritten_files_list.grid(row=9, column=0, columnspan=2, pady=5, padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress.grid(row=10, column=0, pady=5, padx=5, sticky=tk.W)

        # Percent complete label and current directory
        self.percent_label = tk.Label(root, text="0%", anchor="w", width=10)
        self.percent_label.grid(row=10, column=1, pady=5, padx=5, sticky=tk.W)

        self.current_dir_label = tk.Label(root, text="Current Directory: N/A", anchor="w", width=100)
        self.current_dir_label.grid(row=11, column=0, columnspan=2, pady=5, padx=5, sticky=tk.W)

        # Buttons to start, pause, and stop the copy process
        self.start_copy_btn = tk.Button(root, text="Start Copying", command=self.start_copy)
        self.start_copy_btn.grid(row=12, column=0, pady=10)

        self.pause_copy_btn = tk.Button(root, text="Pause Copy", command=self.pause_copy)
        self.pause_copy_btn.grid(row=12, column=1, pady=10)

        self.stop_copy_btn = tk.Button(root, text="Stop Copy", command=self.stop_copy)
        self.stop_copy_btn.grid(row=12, column=2, pady=10)

        # Status bar with file counts and error count
        self.status_label = tk.Label(root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.grid(row=13, column=0, sticky=tk.W + tk.E, ipady=2)

        self.file_counts_label = tk.Label(root, text="New Files: 0 | Overwritten Files: 0 | Errors: 0", bd=1,
                                          relief=tk.SUNKEN, anchor=tk.W)
        self.file_counts_label.grid(row=13, column=1, columnspan=2, sticky=tk.W + tk.E, ipady=2)

        # Log file path
        self.log_file_path = "file_copy_errors.log"

    def select_source_directory(self):
        self.src_dir = filedialog.askdirectory()
        if self.src_dir:
            self.src_dir_label.config(text=self.src_dir)
            messagebox.showinfo("Selected Source", f"Source directory selected: {self.src_dir}")

    def select_destination_directory(self):
        self.dst_dir = filedialog.askdirectory()
        if self.dst_dir:
            self.dst_dir_label.config(text=self.dst_dir)
            messagebox.showinfo("Selected Destination", f"Destination directory selected: {self.dst_dir}")

    def start_copy(self):
        if not self.src_dir or not self.dst_dir:
            messagebox.showwarning("Directories Not Selected", "Please select both source and destination directories.")
            return

        # Reset counts and clear log file
        self.new_files_count = 0
        self.overwritten_files_count = 0
        self.error_count = 0
        self.clear_log_file()

        # Reset stop and pause events
        self.stop_event.clear()
        self.pause_event.set()

        # Start file copying in a separate thread to avoid blocking the UI
        copy_thread = Thread(target=self.copy_files)
        copy_thread.start()

    def pause_copy(self):
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.pause_copy_btn.config(text="Resume Copy")
        else:
            self.pause_event.set()
            self.pause_copy_btn.config(text="Pause Copy")

    def stop_copy(self):
        self.stop_event.set()
        self.pause_event.set()  # Resume if paused to allow stopping
        self.status_label.config(text="Stopping...")

    def clear_log_file(self):
        """Clear the log file at the start of each run."""
        with open(self.log_file_path, "w") as log_file:
            log_file.write("")

    def log_error(self, message):
        """Log errors to a file and update error count."""
        with open(self.log_file_path, "a") as log_file:
            log_file.write(message + "\n\n")
        self.error_count += 1
        self.update_file_counts()

    def get_exclude_dirs(self):
        """Return a list of directories to exclude based on the user's input."""
        exclude_input = self.exclude_entry.get()
        if exclude_input:
            exclude_dirs = [d.strip() for d in exclude_input.split(",")]
            return [os.path.join(self.src_dir, d) for d in exclude_dirs]
        return []

    def copy_files(self):
        # Clear previous lists
        self.copied_files_list.delete(0, tk.END)
        self.overwritten_files_list.delete(0, tk.END)
        self.progress['value'] = 0
        self.update_file_counts()

        exclude_dirs = self.get_exclude_dirs()

        try:
            files_processed = 0
            total_files = 0
            for dirpath, _, filenames in os.walk(self.src_dir):
                if not any(dirpath.startswith(exclude) for exclude in exclude_dirs):
                    total_files += len(filenames)

            current_directory = None
            for dirpath, _, filenames in os.walk(self.src_dir):
                if self.stop_event.is_set():
                    self.status_label.config(text="Copying Stopped.")
                    return

                if not any(dirpath.startswith(exclude) for exclude in exclude_dirs):
                    if current_directory != dirpath:
                        current_directory = dirpath
                        self.current_dir_label.config(text=f"Current Directory: {current_directory}")

                    for file in filenames:
                        src_file = os.path.join(dirpath, file)
                        rel_path = os.path.relpath(src_file, self.src_dir)
                        dst_file = os.path.join(self.dst_dir, rel_path)

                        try:
                            if self.pause_event.is_set():  # Pause if requested
                                if self.copy_mode.get() == "overwrite_all":
                                    self.copy_file(src_file, dst_file)
                                elif self.copy_mode.get() == "copy_new":
                                    if not os.path.exists(dst_file):
                                        self.copy_file(src_file, dst_file)
                                elif self.copy_mode.get() == "copy_newer":
                                    if os.path.exists(dst_file):
                                        if os.path.getmtime(src_file) > os.path.getmtime(dst_file):
                                            self.copy_file(src_file, dst_file, overwrite=True)
                                    else:
                                        self.copy_file(src_file, dst_file)

                                files_processed += 1
                                # Update status, progress, and percent complete
                                percent_complete = (files_processed / total_files) * 100
                                self.progress['value'] = percent_complete
                                self.percent_label.config(text=f"{percent_complete:.0f}%")
                                self.status_label.config(text=f"Files Processed: {files_processed}/{total_files}")
                                self.root.update_idletasks()

                            else:
                                self.pause_event.wait()  # Wait until unpaused

                        except Exception as e:
                            # Log the error and continue
                            self.log_error(f"Error copying {src_file} to {dst_file}: {e}")
                            self.status_label.config(text=f"Error encountered. See log.")

            messagebox.showinfo("Completed", f"File copy completed! {files_processed} files processed.")
            self.status_label.config(text="Completed")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.status_label.config(text="Error during file copy.")

    def copy_file(self, src_file, dst_file, overwrite=False):
        dst_dir = os.path.dirname(dst_file)
        os.makedirs(dst_dir, exist_ok=True)
        if not os.path.exists(dst_file):  # New file
            shutil.copy2(src_file, dst_file)
            self.copied_files_list.insert(tk.END, dst_file)
            self.new_files_count += 1
        elif overwrite:  # Overwriting existing file
            shutil.copy2(src_file, dst_file)
            self.overwritten_files_list.insert(tk.END, dst_file)
            self.overwritten_files_count += 1
        else:  # If not overwriting, treat as a new file
            shutil.copy2(src_file, dst_file)
            self.copied_files_list.insert(tk.END, dst_file)
            self.new_files_count += 1

        # Update file counts
        self.update_file_counts()

    def update_file_counts(self):
        self.file_counts_label.config(
            text=f"New Files: {self.new_files_count} | Overwritten Files: {self.overwritten_files_count} | Errors: {self.error_count}")


if __name__ == "__main__":
    root = tk.Tk()
    app = FileCopyApp(root)
    root.mainloop()
