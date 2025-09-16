import os
import sys
import platform

# macOS Retina display fix (optional, improves scaling on Mac)
if platform.system() == "Darwin":
    try:
        from ctypes import cdll
        cdll.LoadLibrary("/System/Library/Frameworks/Tk.framework/Tk")
    except Exception:
        pass

from ui.main_app import CalorieProApp
from core.db import setup_database

def main():
    """Main function to set up and run the application."""
    # Ensure the database is set up
    setup_database()

    # Create and run the application
    app = CalorieProApp()
    app.mainloop()

if __name__ == "__main__":
    main()
