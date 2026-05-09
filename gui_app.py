#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phone Tracker GUI App
A simple GUI wrapper for the Phone Tracker CLI tool
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import subprocess
import sys
import os
import threading
import queue

class PhoneTrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Phone Number Tracker v5.0")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Queue for thread communication
        self.queue = queue.Queue()

        self.create_widgets()
        self.check_dependencies()

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="🔎 Phone Number Tracker",
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Phone number input
        ttk.Label(main_frame, text="Phone Number:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.phone_entry = ttk.Entry(main_frame, width=30)
        self.phone_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        self.phone_entry.insert(0, "+919876543210")  # Example

        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Scan Options", padding="5")
        options_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        self.quick_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Quick Scan (basic info only)",
                       variable=self.quick_var).grid(row=0, column=0, sticky=tk.W)

        self.skip_live_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Skip Live Location",
                       variable=self.skip_live_var).grid(row=0, column=1, sticky=tk.W)

        self.skip_osint_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Skip OSINT Probes",
                       variable=self.skip_osint_var).grid(row=1, column=0, sticky=tk.W)

        self.skip_deep_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Skip Deep OSINT",
                       variable=self.skip_deep_var).grid(row=1, column=1, sticky=tk.W)

        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=10)

        self.run_button = ttk.Button(buttons_frame, text="Run Scan",
                                   command=self.run_scan)
        self.run_button.grid(row=0, column=0, padx=5)

        ttk.Button(buttons_frame, text="Clear Output",
                  command=self.clear_output).grid(row=0, column=1, padx=5)

        ttk.Button(buttons_frame, text="Save Output",
                  command=self.save_output).grid(row=0, column=2, padx=5)

        # Output area
        ttk.Label(main_frame, text="Output:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.output_text = scrolledtext.ScrolledText(main_frame, height=20, wrap=tk.WORD)
        self.output_text.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var,
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))

    def check_dependencies(self):
        """Check if phone_tracker.py exists"""
        if not os.path.exists("phone_tracker.py"):
            messagebox.showerror("Error", "phone_tracker.py not found in current directory!")
            self.root.quit()

    def run_scan(self):
        phone = self.phone_entry.get().strip()
        if not phone:
            messagebox.showerror("Error", "Please enter a phone number!")
            return

        # Build command
        cmd = [sys.executable, "phone_tracker.py", phone]

        if self.quick_var.get():
            cmd.append("--quick")
        if self.skip_live_var.get():
            cmd.append("--skip-live")
        if self.skip_osint_var.get():
            cmd.append("--skip-osint")
        if self.skip_deep_var.get():
            cmd.append("--skip-deep")

        # Disable button and show status
        self.run_button.config(state="disabled")
        self.status_var.set("Running scan...")
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, f"Running command: {' '.join(cmd)}\n\n")

        # Run in thread
        thread = threading.Thread(target=self.run_command, args=(cmd,))
        thread.daemon = True
        thread.start()

        # Check queue periodically
        self.root.after(100, self.check_queue)

    def run_command(self, cmd):
        try:
            # Change to script directory if needed
            cwd = os.getcwd()

            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Read output line by line
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.queue.put(output.strip())

            rc = process.poll()
            self.queue.put(f"\nProcess completed with return code: {rc}")

        except Exception as e:
            self.queue.put(f"Error running command: {str(e)}")

    def check_queue(self):
        try:
            while True:
                line = self.queue.get_nowait()
                self.output_text.insert(tk.END, line + "\n")
                self.output_text.see(tk.END)
        except queue.Empty:
            pass

        # Check if still running
        if self.queue.empty():
            self.run_button.config(state="normal")
            self.status_var.set("Ready")
        else:
            self.root.after(100, self.check_queue)

    def clear_output(self):
        self.output_text.delete(1.0, tk.END)

    def save_output(self):
        content = self.output_text.get(1.0, tk.END)
        if not content.strip():
            messagebox.showwarning("Warning", "No output to save!")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Output saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")

def main():
    root = tk.Tk()
    app = PhoneTrackerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()