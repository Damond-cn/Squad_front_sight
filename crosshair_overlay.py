import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage, filedialog # Import filedialog
from PIL import Image, ImageTk
import os
import sys
# Note: 'keyboard' library might require administrator privileges on some systems
# If you have issues with the hotkey, try running the script as admin.
try:
    import keyboard # Use 'pip install keyboard'
    # Check if running in a standard environment where keyboard can hook
    if not sys.stdout.isatty():
         print("Warning: Hotkey functionality may be limited when not run from a standard terminal.")
except ImportError:
    keyboard = None
    print("Warning: 'keyboard' library not found. Hotkey functionality is disabled.")
except Exception as e:
     keyboard = None
     print(f"Warning: Failed to import or initialize 'keyboard' library: {e}\nHotkey functionality is disabled.")


# --- Configuration ---
# We'll start with a default, but the user can select a different folder
DEFAULT_IMG_DIR = "./img"
TOGGLE_HOTKEY = "f10"
# A color unlikely to be in your crosshair PNGs, used for transparency keying
# If your crosshairs use bright green, choose a different color like 'magenta'
TRANSPARENT_COLOR = 'lime green'


# --- Global Variables ---
root = None
overlay_window = None
overlay_label = None
overlay_photo = None # Keep a reference to avoid garbage collection
overlay_visible = False
current_image_path = None
current_img_dir = DEFAULT_IMG_DIR # Use a variable for the current image directory

# GUI elements we need to access from functions
folder_entry = None
image_combo = None


# --- Functions ---

def get_screen_resolution():
    """Gets the primary screen resolution using Tkinter."""
    # Create a temporary root window if none exists yet for screen info
    temp_root = None
    # Check if default_root exists (means mainloop is running or root created)
    # or if root is explicitly created but not yet mainlooping
    if not tk._default_root and root is None:
        temp_root = tk.Tk()
        temp_root.withdraw() # Hide the temp window

    try:
        # Use tk._default_root if available (after root.mainloop() starts implicitly)
        # or use the explicitly created root if mainloop hasn't started yet
        source_widget = tk._default_root if tk._default_root else root
        if source_widget:
             width = source_widget.winfo_screenwidth()
             height = source_widget.winfo_screenheight()
             return width, height
        else:
             # Fallback if somehow neither is available (shouldn't happen in normal flow)
             print("Warning: Could not get screen resolution from Tkinter sources.")
             # Provide a default or raise error
             return 1920, 1080 # Just an example fallback
    finally:
        if temp_root:
            temp_root.destroy()


def load_image_list(directory):
    """Loads PNG files from the specified directory."""
    if not os.path.isdir(directory):
        # print(f"Image directory '{directory}' not found or not a directory.") # Suppress error message here, handle in select_folder/create_gui
        return []
    try:
        # Use absolute path to avoid issues if the current working directory changes
        abs_dir = os.path.abspath(directory)
        files = [f for f in os.listdir(abs_dir) if f.lower().endswith('.png')]
        # Sort files alphabetically for consistent ordering
        files.sort()
        print(f"Loaded {len(files)} PNG files from '{abs_dir}'.")
        return files
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read image directory '{directory}':\n{e}")
        return []

def create_or_update_overlay(image_path):
    """Creates or updates the overlay window with the given image."""
    global overlay_window, overlay_label, overlay_photo, current_image_path, overlay_visible

    try:
        # Load image with Pillow
        pil_image = Image.open(image_path)
        img_width, img_height = pil_image.size

        # Get screen resolution
        screen_width, screen_height = get_screen_resolution()

        # --- Resolution Check ---
        # We allow images smaller than the screen, but not larger, and check for mismatch
        if img_width > screen_width or img_height > screen_height:
             messagebox.showerror("Resolution Mismatch",
                                 f"Image dimensions ({img_width}x{img_height}) are larger than "
                                 f"screen resolution ({screen_width}x{screen_height}).\n"
                                 "Images must be equal to or smaller than screen resolution.")
             pil_image.close() # Close the image file
             return False
        # Check for exact match if that's a strict requirement
        # if img_width != screen_width or img_height != screen_height:
        #    messagebox.showwarning("Resolution Warning",
        #                         f"Image dimensions ({img_width}x{img_height}) do not exactly match "
        #                         f"screen resolution ({screen_width}x{screen_height}).\n"
        #                         "The image will be displayed at its original size, centered.")
            # If we allow smaller images, we'll need to center the label in the window

        # --- Load image for Tkinter ---
        # Keep a reference to prevent garbage collection!
        overlay_photo = ImageTk.PhotoImage(pil_image)
        current_image_path = image_path # Store path for potential re-application
        pil_image.close() # Close the image file as ImageTk.PhotoImage has the necessary data


        if overlay_window is None or not overlay_window.winfo_exists():
            # --- Create Overlay Window ---
            overlay_window = tk.Toplevel(root)
            overlay_window.overrideredirect(True)  # No border, title bar, etc.
            # Set geometry to screen resolution
            overlay_window.geometry(f"{screen_width}x{screen_height}+0+0") # Fullscreen, top-left corner
            overlay_window.lift()
            overlay_window.wm_attributes("-topmost", True) # Keep on top

            # --- Make window background transparent ---
            overlay_window.config(bg=TRANSPARENT_COLOR)
            overlay_window.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)

            # --- Create Label to hold the image ---
            # The label background must also match the transparent color
            overlay_label = tk.Label(overlay_window, image=overlay_photo, bg=TRANSPARENT_COLOR)
            # Use place to center the image if it's smaller than the screen
            overlay_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

            # Hide initially, toggle will show it
            overlay_window.withdraw()
            overlay_visible = False
            print("Overlay window created.")

        else:
            # --- Update Existing Overlay Window ---
            overlay_label.config(image=overlay_photo)
            # Ensure geometry is still correct (though it shouldn't change if res matches)
            overlay_window.geometry(f"{screen_width}x{screen_height}+0+0")
            # Re-center the label in case the new image size is different
            overlay_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
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
        current_image_path = None # Clear the path of the failed image
        return False

def apply_crosshair():
    """Called when the 'Apply Crosshair' button is clicked."""
    global overlay_visible # Need to modify overlay_visible if we show the window

    selected_image = image_combo.get()
    if not selected_image:
        messagebox.showwarning("No Selection", "Please select a crosshair image.")
        return

    # Use the current_img_dir to construct the full path
    full_path = os.path.join(current_img_dir, selected_image)

    if create_or_update_overlay(full_path):
        messagebox.showinfo("Success", f"Crosshair '{selected_image}' applied.\nPress {TOGGLE_HOTKEY.upper()} to toggle visibility.")
        # Make sure it's visible after applying, unless it was already visible
        if overlay_window and not overlay_visible:
             toggle_overlay() # This will make it visible

def toggle_overlay():
    """Shows or hides the overlay window."""
    global overlay_window, overlay_visible
    if overlay_window is None or not overlay_window.winfo_exists():
        print("Toggle ignored: Overlay window does not exist.")
        # Optionally try to re-apply the last known good image if desired
        # This might happen if the overlay was closed manually or failed
        if current_image_path:
           print(f"Attempting to recreate overlay using last image: {os.path.basename(current_image_path)}")
           if create_or_update_overlay(current_image_path):
                # If recreation succeeds, ensure it's shown
                overlay_visible = False # Set to False so the toggle logic shows it
                toggle_overlay() # Call again to show
           else:
                print("Recreation failed.")
        return

    if overlay_visible:
        overlay_window.withdraw() # Hide the window
        overlay_visible = False
        # print(f"{TOGGLE_HOTKEY.upper()} pressed: Overlay hidden.") # Avoid flooding console on rapid presses
    else:
        overlay_window.deiconify() # Show the window
        # Bring to front - may need system-specific adjustments for games
        overlay_window.lift()
        overlay_window.wm_attributes("-topmost", True) # Re-assert topmost
        overlay_visible = True
        # print(f"{TOGGLE_HOTKEY.upper()} pressed: Overlay shown.") # Avoid flooding console

def setup_hotkey():
    """Sets up the global hotkey listener."""
    if keyboard is None:
        print("Hotkey setup skipped: 'keyboard' library not available.")
        return

    try:
        # Use lambda to avoid issues with arguments if toggle_overlay expected none
        # suppress=True prevents the key event from being passed to other applications
        keyboard.add_hotkey(TOGGLE_HOTKEY, lambda: toggle_overlay(), suppress=True)
        print(f"Hotkey '{TOGGLE_HOTKEY.upper()}' registered. Press it to toggle the crosshair overlay.")
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
        if keyboard:
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

def select_folder():
    """Opens a dialog to select the image folder and updates the GUI."""
    global current_img_dir # Need to modify the global variable
    selected_directory = filedialog.askdirectory(
        title="Select Crosshair Image Folder",
        initialdir=current_img_dir # Start the dialog in the current directory
    )

    # askdirectory returns an empty string if the user cancels
    if selected_directory:
        current_img_dir = selected_directory
        folder_entry.config(state='normal') # Allow modification
        folder_entry.delete(0, tk.END)
        folder_entry.insert(0, current_img_dir)
        folder_entry.config(state='readonly') # Make readonly again

        # Now load images from the new directory and update the combobox
        refresh_image_list_in_gui()
        print(f"Image directory updated to: {current_img_dir}")
    else:
        print("Folder selection cancelled.")

def refresh_image_list_in_gui():
    """Loads images from the current directory and updates the combobox."""
    global image_combo # Need to access the global combobox
    image_files = load_image_list(current_img_dir)
    image_combo['values'] = image_files
    if image_files:
         image_combo.current(0) # Select the first image
         # Enable apply button if it was potentially disabled
         # apply_button.config(state='normal') # Assuming an apply button exists and is accessible
    else:
        image_combo.set('No PNG files found') # Or just ''
        # Disable apply button if no files are found
        # apply_button.config(state='disabled') # Assuming an apply button exists and is accessible
        print(f"No PNG files found in '{current_img_dir}'.")


# --- GUI Setup ---
def create_gui():
    global root, folder_entry, image_combo # Make GUI elements accessible globally

    root = tk.Tk()
    root.title("Crosshair Selector")
    # root.geometry("400x200") # Optional: Set initial size, adjust as needed

    # --- Folder Selection Frame ---
    folder_frame = ttk.Frame(root, padding="10")
    folder_frame.pack(fill=tk.X, pady=5) # Fill horizontally

    folder_label = ttk.Label(folder_frame, text="Image Folder:")
    folder_label.pack(side=tk.LEFT, padx=(0, 5)) # Align left

    # Entry to display the selected path
    folder_entry = ttk.Entry(folder_frame, width=40, state='readonly') # Start as readonly
    folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

    # Button to open folder dialog
    select_folder_button = ttk.Button(folder_frame, text="Select Folder", command=select_folder)
    select_folder_button.pack(side=tk.LEFT)


    # --- Image Selection Frame ---
    image_frame = ttk.Frame(root, padding="10")
    image_frame.pack(fill=tk.BOTH, expand=True, pady=5)

    image_label = ttk.Label(image_frame, text="Select Crosshair Image:")
    image_label.pack(pady=(0, 5)) # Add some space below the label

    # Combobox for image selection
    # Initial population will happen after the GUI is created
    image_combo = ttk.Combobox(image_frame, values=[], state="readonly", width=40)
    image_combo.pack(pady=(0, 10)) # Add some space below the combobox

    # Apply Button
    apply_button = ttk.Button(image_frame, text="Apply Crosshair", command=apply_crosshair)
    apply_button.pack(pady=(0, 5)) # Add some space below the button


    # --- Initial State Setup ---
    # Set the initial folder path in the entry
    folder_entry.config(state='normal')
    folder_entry.insert(0, current_img_dir)
    folder_entry.config(state='readonly')

    # Load the initial list of images for the combobox
    refresh_image_list_in_gui()


    # --- Hotkey and Close Protocol ---
    root.protocol("WM_DELETE_WINDOW", on_close) # Register cleanup function


    # --- Center the window ---
    # Needs update_idletasks to calculate correct window size
    root.update_idletasks()
    screen_w, screen_h = get_screen_resolution()
    window_size = tuple(int(_) for _ in root.geometry().split('+')[0].split('x'))
    x = screen_w/2 - window_size[0]/2
    y = screen_h/2 - window_size[1]/2
    root.geometry("+%d+%d" % (x, y))

    return root


# --- Main Execution ---
if __name__ == "__main__":

    # Basic check if running as admin (Windows only check here for simplicity)
    is_admin = False
    if sys.platform == "win32":
        try:
            import ctypes
            is_admin = (hasattr(ctypes, 'windll') and ctypes.windll.shell32.IsUserAnAdmin() != 0)
        except Exception:
             pass # Ignore if ctypes is not available

    if not is_admin and sys.platform == "win32":
        print("Warning: Script not running as administrator. Global hotkey (F10) might not work reliably in some applications.")
        # Optionally display a warning message box
        # messagebox.showwarning("Admin Rights", "Run this script as an administrator for the F10 hotkey to work reliably.")


    # Create the main GUI
    main_window = create_gui()

    # Setup the hotkey *after* the GUI is created but before mainloop starts
    # This ensures Tkinter's internal setup is done first
    setup_hotkey()

    # Start the Tkinter event loop
    print("Starting GUI main loop...")
    main_window.mainloop()

    # The script will pause here until the main window is closed.
    # The on_close function handles cleanup before the script fully exits.
    print("Application finished.")