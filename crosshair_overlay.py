import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage
from PIL import Image, ImageTk
import os
import sys
import keyboard  # Use 'pip install keyboard'

# --- Configuration ---
IMG_DIR = "./img"
TOGGLE_HOTKEY = "f10"
TRANSPARENT_COLOR = 'lime green' # A color unlikely to be in your crosshair PNGs

# --- Global Variables ---
root = None
overlay_window = None
overlay_label = None
overlay_photo = None # Keep a reference to avoid garbage collection
overlay_visible = False
current_image_path = None

# --- Functions ---

def get_screen_resolution():
    """Gets the primary screen resolution using Tkinter."""
    # Create a temporary root window if none exists yet for screen info
    temp_root = None
    if not tk._default_root:
        temp_root = tk.Tk()
        temp_root.withdraw() # Hide the temp window

    try:
        width = tk._default_root.winfo_screenwidth()
        height = tk._default_root.winfo_screenheight()
        return width, height
    finally:
        if temp_root:
            temp_root.destroy()


def load_image_list():
    """Loads PNG files from the IMG_DIR."""
    if not os.path.exists(IMG_DIR):
        messagebox.showerror("Error", f"Image directory '{IMG_DIR}' not found.\nPlease create it and add PNG crosshairs.")
        return []
    try:
        files = [f for f in os.listdir(IMG_DIR) if f.lower().endswith('.png')]
        return files
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read image directory '{IMG_DIR}':\n{e}")
        return []

def create_or_update_overlay(image_path):
    """Creates or updates the overlay window with the given image."""
    global overlay_window, overlay_label, overlay_photo, current_image_path, overlay_visible

    try:
        # Load image with Pillow to check dimensions first
        pil_image = Image.open(image_path)
        img_width, img_height = pil_image.size

        # Get screen resolution
        screen_width, screen_height = get_screen_resolution()

        # --- Resolution Check ---
        if img_width != screen_width or img_height != screen_height:
            messagebox.showerror("Resolution Mismatch",
                                 f"Image dimensions ({img_width}x{img_height}) do not match "
                                 f"screen resolution ({screen_width}x{screen_height}).")
            return False

        # --- Load image for Tkinter ---
        # Keep a reference to prevent garbage collection!
        overlay_photo = ImageTk.PhotoImage(pil_image)
        current_image_path = image_path # Store path for potential re-application

        if overlay_window is None or not overlay_window.winfo_exists():
            # --- Create Overlay Window ---
            overlay_window = tk.Toplevel(root)
            overlay_window.overrideredirect(True)  # No border, title bar, etc.
            overlay_window.geometry(f"{screen_width}x{screen_height}+0+0") # Fullscreen, top-left corner
            overlay_window.lift()
            overlay_window.wm_attributes("-topmost", True) # Keep on top

            # --- Make window background transparent ---
            # The parts of the window *not* covered by the label will be transparent
            overlay_window.config(bg=TRANSPARENT_COLOR)
            overlay_window.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)

            # --- Create Label to hold the image ---
            # The label background must also match the transparent color
            overlay_label = tk.Label(overlay_window, image=overlay_photo, bg=TRANSPARENT_COLOR)
            overlay_label.pack()

            # Hide initially, toggle will show it
            overlay_window.withdraw()
            overlay_visible = False
            print("Overlay window created.")

        else:
            # --- Update Existing Overlay Window ---
            overlay_label.config(image=overlay_photo)
            # Ensure geometry is still correct (though it shouldn't change if res matches)
            overlay_window.geometry(f"{screen_width}x{screen_height}+0+0")
            print("Overlay image updated.")

        return True # Indicate success

    except FileNotFoundError:
         messagebox.showerror("Error", f"Image file not found:\n{image_path}")
         return False
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load or display image:\n{e}")
        # Clean up potentially broken overlay
        if overlay_window and overlay_window.winfo_exists():
            overlay_window.destroy()
        overlay_window = None
        overlay_label = None
        overlay_photo = None
        overlay_visible = False
        return False

def apply_crosshair():
    """Called when the 'Apply Crosshair' button is clicked."""
    selected_image = image_combo.get()
    if not selected_image:
        messagebox.showwarning("No Selection", "Please select a crosshair image.")
        return

    full_path = os.path.join(IMG_DIR, selected_image)
    if create_or_update_overlay(full_path):
        messagebox.showinfo("Success", f"Crosshair '{selected_image}' applied.\nPress {TOGGLE_HOTKEY.upper()} to toggle visibility.")
        # Make sure it's visible after applying, unless it was already visible
        if not overlay_visible and overlay_window:
             toggle_overlay() # This will make it visible


def toggle_overlay():
    """Shows or hides the overlay window."""
    global overlay_window, overlay_visible
    if overlay_window is None or not overlay_window.winfo_exists():
        print("Toggle ignored: Overlay window does not exist.")
        # Optionally try to re-apply the last known good image if desired
        # if current_image_path:
        #    print("Attempting to recreate overlay...")
        #    if create_or_update_overlay(current_image_path):
        #         overlay_visible = False # Start hidden after recreate
        #         toggle_overlay() # Call again to show
        return

    if overlay_visible:
        overlay_window.withdraw() # Hide the window
        overlay_visible = False
        print(f"{TOGGLE_HOTKEY.upper()} pressed: Overlay hidden.")
    else:
        overlay_window.deiconify() # Show the window
        overlay_window.lift() # Ensure it's raised (might help with some focus issues)
        overlay_window.wm_attributes("-topmost", True) # Re-assert topmost
        overlay_visible = True
        print(f"{TOGGLE_HOTKEY.upper()} pressed: Overlay shown.")


def setup_hotkey():
    """Sets up the global hotkey listener."""
    try:
        # Use lambda to avoid issues with arguments if toggle_overlay expected none
        keyboard.add_hotkey(TOGGLE_HOTKEY, lambda: toggle_overlay())
        print(f"Hotkey '{TOGGLE_HOTKEY.upper()}' registered. Listening...")
        # Add a note about admin rights if detection fails later or is common
        # Note: keyboard library might need admin rights to capture global keys.
    except Exception as e:
         messagebox.showerror("Hotkey Error",
                              f"Failed to register hotkey '{TOGGLE_HOTKEY.upper()}'.\n"
                              f"Error: {e}\n\n"
                              "Try running the script as an administrator.")
         # Optionally, disable hotkey functionality or exit
         print(f"Hotkey registration failed: {e}")


def on_close():
    """Cleanup actions when the main GUI window is closed."""
    print("Closing application...")
    try:
        print("Unhooking keyboard listener...")
        keyboard.unhook_all() # Stop listening for hotkeys
    except Exception as e:
        print(f"Error unhooking keyboard: {e}") # Log error but continue closing

    global overlay_window
    if overlay_window and overlay_window.winfo_exists():
        print("Destroying overlay window...")
        overlay_window.destroy()
    if root:
        print("Destroying main GUI window...")
        root.destroy()
    print("Exiting.")


# --- GUI Setup ---
def create_gui():
    global root, image_combo # Make GUI elements accessible globally if needed

    root = tk.Tk()
    root.title("Crosshair Selector")
    # root.geometry("350x150") # Optional: Set initial size

    # Make sure IMG_DIR exists before proceeding
    if not os.path.isdir(IMG_DIR):
        os.makedirs(IMG_DIR, exist_ok=True)
        print(f"Created image directory: {IMG_DIR}")
        # You might want to inform the user to add images now
        messagebox.showinfo("Directory Created", f"Image directory '{IMG_DIR}' was created.\nPlease add your PNG crosshair files there and restart the application.")


    # Frame for better layout
    frame = ttk.Frame(root, padding="10")
    frame.pack(expand=True, fill=tk.BOTH)

    # Label
    label = ttk.Label(frame, text="Select Crosshair Image:")
    label.pack(pady=5)

    # Combobox for image selection
    image_files = load_image_list()
    image_combo = ttk.Combobox(frame, values=image_files, state="readonly", width=30)
    if image_files:
        image_combo.current(0) # Select the first image by default
    image_combo.pack(pady=5)

    # Apply Button
    apply_button = ttk.Button(frame, text="Apply Crosshair", command=apply_crosshair)
    apply_button.pack(pady=10)

    # Refresh Button
    def refresh_list():
        images = load_image_list()
        image_combo['values'] = images
        if images:
             image_combo.current(0)
        else:
            image_combo.set('')
        print("Image list refreshed.")

    refresh_button = ttk.Button(frame, text="Refresh List", command=refresh_list)
    refresh_button.pack(pady=2)



    root.protocol("WM_DELETE_WINDOW", on_close) # Register cleanup function


    root.update_idletasks()
    screen_w, screen_h = get_screen_resolution()
    size = tuple(int(_) for _ in root.geometry().split('+')[0].split('x'))
    x = screen_w/2 - size[0]/2
    y = screen_h/2 - size[1]/2
    root.geometry("+%d+%d" % (x, y))

    return root


# --- Main Execution ---
if __name__ == "__main__":

    try:
        is_admin = os.getuid() == 0 # Linux/macOS specific
    except AttributeError:
        try:
            # Windows specific
            is_admin = os.environ.get("PROCESSOR_ARCHITECTURE") == "AMD64" or \
                       os.environ.get("PROCESSOR_ARCHITEW6432") is not None or \
                       (hasattr(ctypes, 'windll') and ctypes.windll.shell32.IsUserAnAdmin() != 0)
        except Exception: # Catch potential errors if ctypes isn't available or fails
             is_admin = False # Assume not admin if check fails

    if not is_admin and sys.platform == "win32":
        print("Warning: Script not running as administrator. Global hotkey (F10) might not work.")
        # Optionally display a warning message box
        # messagebox.showwarning("Admin Rights", "Run this script as an administrator for the F10 hotkey to work reliably.")


    # Create the main GUI
    main_window = create_gui()

    # Setup the hotkey *after* the Tkinter loop is potentially ready
    # but before starting the main loop.
    setup_hotkey()

    # Start the Tkinter event loop
    print("Starting GUI main loop...")
    main_window.mainloop()

    # The script will pause here until the main window is closed.
    # The on_close function handles cleanup.
    print("Application finished.")