import json
import os
import time
import pyautogui
import pyperclip  # Make sure this is installed: pip install pyperclip
import keyboard  # Make sure this is installed: pip install keyboard
import threading
from datetime import datetime

# --- Configuration ---
# File to store your keywords and replacements
PROMPTS_FILE = "prompts.json"

class RealtimeTextReplacer:
    def __init__(self):
        self.prompts = self.load_prompts()
        self.current_buffer = ""
        self.is_replacing = False  # A flag to prevent the script from triggering itself
        self.last_reload_time = datetime.now()  # Track the last reload time
        self.lock = threading.Lock()  # Lock for thread-safe operations
        self.last_file_mod_time = self._get_file_mod_time()  # Track file modification time

    def load_prompts(self) -> dict:
        """Loads keywords and replacements from the JSON file."""
        if os.path.exists(PROMPTS_FILE):
            try:
                with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading prompts file: {e}. Starting with an empty list.")
                return {}
        return {}



    def _get_file_mod_time(self):
        """Returns the modification time of the prompts file, or None if it doesn't exist."""
        if os.path.exists(PROMPTS_FILE):
            return os.path.getmtime(PROMPTS_FILE)
        return None

    def reload_prompts_if_needed(self):
        """Reloads the prompts from the JSON file if it has been modified."""
        current_file_mod_time = self._get_file_mod_time()
        
        # Check if the file has been modified since the last check
        if current_file_mod_time and current_file_mod_time != self.last_file_mod_time:
            print("Detected changes in prompts.json, reloading...")
            new_prompts = self.load_prompts()
            # Only update if there are changes in the content
            if new_prompts != self.prompts:
                with self.lock:  # Acquire lock when updating prompts
                    self.prompts = new_prompts
                print("Prompts reloaded successfully.")
            self.last_file_mod_time = current_file_mod_time
        else:
            # If file hasn't changed, check if 10 seconds have passed to periodically update mod time
            current_time = datetime.now()
            if (current_time - self.last_reload_time).seconds >= 10:
                self.last_reload_time = current_time
                # Update the stored modification time to catch any updates we might have missed
                self.last_file_mod_time = self._get_file_mod_time()

    def on_key_event(self, event):
        """This function is called every time a key is pressed."""
        if self.is_replacing:
            return  # Ignore key presses while a replacement is happening

        # Only process key down events, not key up events
        if event.event_type == keyboard.KEY_DOWN:
            # Add typed characters to our buffer
            if len(event.name) == 1:  # Regular character keys
                self.current_buffer += event.name
            # The SPACE key is our trigger to check for a keyword
            elif event.name == 'space':
                self.current_buffer += ' '
                self.check_for_replacement()
            # Handle backspace to keep the buffer accurate
            elif event.name == 'backspace':
                self.current_buffer = self.current_buffer[:-1]
            
            # Keep the buffer from getting too long
            if len(self.current_buffer) > 100:
                self.current_buffer = self.current_buffer[-100:]

    def check_for_replacement(self):
        """Checks if the buffer ends with a known keyword followed by a space."""
        if self.is_replacing:
            return

        # Acquire lock when accessing prompts (since reload might update it)
        with self.lock:
            # Create a local copy of prompts to minimize lock time
            local_prompts = dict(self.prompts)
        
        # Sort keywords by length (longest first) to avoid partial matches
        sorted_keywords = sorted(local_prompts.keys(), key=len, reverse=True)
        
        for keyword in sorted_keywords:
            # The trigger is the keyword itself, followed by a space
            trigger_phrase = keyword + ' '
            if self.current_buffer.endswith(trigger_phrase):
                print(f"--- Match Found! Keyword: '{keyword}' ---")
                self.perform_replacement(keyword)
                return # Exit after the first match is found and replaced

    def perform_replacement(self, keyword: str):
        """Replaces the typed keyword with the desired text using your specific sequence."""
        self.is_replacing = True  # Set the flag to block on_key_event
        
        # Get the replacement text with lock to prevent changes during replacement
        with self.lock:
            replacement_text = self.prompts[keyword]
        
        # 1. Determine total length to delete (keyword + space character)
        total_length = len(keyword) + 1  # +1 for the space character
        
        # 2. Delete the keyword and space character quickly using the new method
        pyautogui.press('backspace', presses=total_length, interval=0.003)

        # 2.5. Add a small delay to ensure all characters are deleted
        

        # 3. Use the clipboard to paste the replacement text for maximum speed
        print("Pasting replacement text from clipboard...")
        original_clipboard = pyperclip.paste()  # Save what the user had on their clipboard
        try:
            pyperclip.copy(replacement_text)
            pyautogui.hotkey('ctrl', 'v')  # Paste
        finally:
            # IMPORTANT: Restore the user's original clipboard content
            pyperclip.copy(original_clipboard)

        # 4. Clean up and finish
        self.current_buffer = ""  # Reset the buffer to prevent re-triggering
        print(f"--- Replacement Complete for '{keyword}' ---")
        self.is_replacing = False  # Release the flag



    def start_monitoring(self):
        """Starts the keyboard listener and waits for keywords."""
        print("--- Text Replacer is now active ---")
        print("Type a keyword followed by a SPACE to trigger a replacement.")
        print("Press Ctrl+C in this console to exit the program.")
        
        # Hook the keyboard events
        keyboard.hook(self.on_key_event)
        
        # Keep the script running and reload prompts when file changes
        try:
            while True:
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                self.reload_prompts_if_needed()  # Check for file changes and reload if needed
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt received. Stopping script...")
            keyboard.unhook_all()
            os._exit(0)  # Force exit the program



if __name__ == "__main__":
    # Create an instance of our replacer class
    replacer = RealtimeTextReplacer()
    
    # Start the main monitoring loop
    replacer.start_monitoring()

    print("--- Script has been terminated ---")