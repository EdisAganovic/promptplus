import json
import os
import time
from pynput import keyboard
from pynput.keyboard import Key, Listener
import pyautogui
from typing import Dict
import pyperclip  # Make sure this is installed: pip install pyperclip

# --- Configuration ---
# File to store your keywords and replacements
PROMPTS_FILE = "prompts.json"

# Global listener variable to allow stopping it from anywhere
listener = None

class RealtimeTextReplacer:
    def __init__(self):
        self.prompts = self.load_prompts()
        self.current_buffer = ""
        self.is_replacing = False  # A flag to prevent the script from triggering itself

    def load_prompts(self) -> Dict[str, str]:
        """Loads keywords and replacements from the JSON file."""
        if os.path.exists(PROMPTS_FILE):
            try:
                with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading prompts file: {e}. Starting with an empty list.")
                return {}
        return {}

    def save_prompts(self, prompts: Dict[str, str]) -> None:
        """Saves the current keywords and replacements to the JSON file."""
        try:
            with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(prompts, f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"Error saving prompts file: {e}")

    def add_prompt(self, keyword: str, content: str):
        """Adds a new keyword and replacement, then saves to the file."""
        self.prompts[keyword] = content
        self.save_prompts(self.prompts)
        print(f"Added keyword: '{keyword}'")

    def remove_prompt(self, keyword: str):
        """Removes a keyword, then saves the change."""
        if keyword in self.prompts:
            del self.prompts[keyword]
            self.save_prompts(self.prompts)
            print(f"Removed keyword: '{keyword}'")

    def on_press(self, key):
        """This function is called every time a key is pressed."""
        if self.is_replacing:
            return  # Ignore key presses while a replacement is happening

        try:
            # Add typed characters to our buffer
            if hasattr(key, 'char') and key.char is not None:
                self.current_buffer += key.char
            # The SPACE key is our trigger to check for a keyword
            elif key == Key.space:
                self.current_buffer += ' '
                self.check_for_replacement()
            # Handle backspace to keep the buffer accurate
            elif key == Key.backspace:
                self.current_buffer = self.current_buffer[:-1]
            
            # Keep the buffer from getting too long
            if len(self.current_buffer) > 100:
                self.current_buffer = self.current_buffer[-100:]

        except AttributeError:
            # Ignore special keys that don't have a 'char' attribute
            pass

    def check_for_replacement(self):
        """Checks if the buffer ends with a known keyword followed by a space."""
        if self.is_replacing:
            return

        # Sort keywords by length (longest first) to avoid partial matches
        sorted_keywords = sorted(self.prompts.keys(), key=len, reverse=True)
        
        for keyword in sorted_keywords:
            # The trigger is the keyword itself, followed by a space
            trigger_phrase = keyword + ' '
            if self.current_buffer.endswith(trigger_phrase):
                print(f"--- Match Found! Keyword: '{keyword}' ---")
                self.perform_replacement(keyword)
                return # Exit after the first match is found and replaced

    def perform_replacement(self, keyword: str):
        """Replaces the typed keyword with the desired text using your specific sequence."""
        self.is_replacing = True  # Set the flag to block on_press
        
        replacement_text = self.prompts[keyword]
        
        # 1. Backspace the triggering space character first
        pyautogui.press('backspace')
        time.sleep(0.05)

        # 2. Execute the precise selection and deletion sequence you requested
        print("Executing selection sequence: CTRL+SHIFT -> LEFT -> LEFT -> DELETE")
        
        # Step 1: Press CTRL+SHIFT and hold them
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown('shift')
        time.sleep(0.05)
        
        # Step 2: Press left arrow two times
        pyautogui.press('left')
        pyautogui.press('left')
        
        # Step 3: Release CTRL+SHIFT
        pyautogui.keyUp('shift')
        pyautogui.keyUp('ctrl')
        time.sleep(0.05)
        
        # Step 4: Press DELETE key
        pyautogui.press('delete')
        
        # 3. Use the clipboard to paste the replacement text for maximum speed
        print("Pasting replacement text from clipboard...")
        original_clipboard = pyperclip.paste() # Save what the user had on their clipboard
        try:
            pyperclip.copy(replacement_text)
            time.sleep(0.1)  # Give the system a moment to update the clipboard
            pyautogui.hotkey('ctrl', 'v') # Paste
        finally:
            # IMPORTANT: Restore the user's original clipboard content
            pyperclip.copy(original_clipboard)

        # 4. Clean up and finish
        self.current_buffer = "" # Reset the buffer to prevent re-triggering
        print(f"--- Replacement Complete for '{keyword}' ---")
        self.is_replacing = False # Release the flag

    def on_release(self, key):
        """This function is called when a key is released."""
        # Stop the listener if the ESC key is pressed
        if key == Key.esc:
            print("\nESC key pressed. Stopping script...")
            return False

    def start_monitoring(self):
        """Starts the keyboard listener and waits for keywords."""
        print("--- Text Replacer is now active ---")
        print("Type a keyword followed by a SPACE to trigger a replacement.")
        print("Press ESC to exit.")
        
        # Create and start the listener
        global listener
        listener = Listener(on_press=self.on_press, on_release=self.on_release)
        listener.start()
        listener.join() # Wait for the listener to stop

def setup_initial_prompts(replacer: RealtimeTextReplacer):
    """Adds some example prompts if the file is empty."""
    if not replacer.prompts:
        print("No prompts found. Adding some examples to 'prompts.json'...")
        replacer.add_prompt("@email", "my.personal.email@example.com")
        replacer.add_prompt("@sig", "Best regards,\nYour Name")
        replacer.add_prompt("syc", "Sincerely,\n\nYour Name\nYour Title")
        print("Example prompts have been added.")

if __name__ == "__main__":
    # Create an instance of our replacer class
    replacer = RealtimeTextReplacer()
    
    # Optional: Add example prompts if the JSON file is empty
    setup_initial_prompts(replacer)
    
    # Start the main monitoring loop
    replacer.start_monitoring()

    print("--- Script has been terminated ---")