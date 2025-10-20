import tkinter as tk
from PIL import Image, ImageTk
import os


class SplashScreen(tk.Toplevel):
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.title("Loading...")

        # Remove window decorations
        self.overrideredirect(True)

        # Set window size and position
        width = 400
        height = 300
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Configure the window
        self.configure(bg="#1F2937")

        # Create main frame
        main_frame = tk.Frame(self, bg="#1F2937")
        main_frame.pack(fill="both", expand=True)

        # Try to load the wallet icon
        try:
            if os.path.exists("wallet.png"):
                # Load and resize the image
                img = Image.open("wallet.png")
                img = img.resize((128, 128), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)

                # Create and pack the image label
                icon_label = tk.Label(main_frame, image=photo, bg="#1F2937")
                self.photo = photo  # Keep a reference
                icon_label.pack(pady=20)
        except Exception:
            pass  # If image loading fails, skip it

        # Add title
        title_label = tk.Label(
            main_frame,
            text="Nockchain Wallet",
            font=("Segoe UI", 18, "bold"),
            fg="white",
            bg="#1F2937",
        )
        title_label.pack(pady=10)

        # Add loading text
        self.loading_label = tk.Label(
            main_frame,
            text="Loading...",
            font=("Segoe UI", 10),
            fg="#A5B4FC",
            bg="#1F2937",
        )
        self.loading_label.pack(pady=10)

        # Progress bar (just a frame that changes width)
        self.progress_frame = tk.Frame(main_frame, width=0, height=4, bg="#818CF8")
        self.progress_frame.pack(pady=20)

        # Make sure this window stays on top
        self.lift()
        self.attributes("-topmost", True)

    def update_progress(self, progress, text=None):
        """Update progress bar (0-100) and optionally update text"""
        width = int((progress / 100) * 300)  # 300px is max width
        self.progress_frame.configure(width=width)
        if text:
            self.loading_label.configure(text=text)
        self.update_idletasks()

    def finish(self):
        """Close the splash screen"""
        self.destroy()
