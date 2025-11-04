import json
import os
import time
import pyautogui
import pyperclip  # Make sure this is installed: pip install pyperclip
import keyboard  # Make sure this is installed: pip install keyboard

# --- Configuration ---
# File to store your keywords and replacements
PROMPTS_FILE = "prompts.json"

class RealtimeTextReplacer:
    def __init__(self):
        self.prompts = self.load_prompts()
        self.current_buffer = ""
        self.is_replacing = False  # A flag to prevent the script from triggering itself

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

    def save_prompts(self, prompts: dict) -> None:
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
        self.is_replacing = True  # Set the flag to block on_key_event
        
        replacement_text = self.prompts[keyword]
        
        # 1. Determine total length to delete (keyword + space character)
        total_length = len(keyword) + 1  # +1 for the space character
        
        # 2. Delete the keyword and space character in one loop
        for _ in range(total_length):
            pyautogui.press('backspace')

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

    def stop_listener(self, event):
        """This function is called when the ESC key is pressed."""
        if event.name == 'esc' and event.event_type == keyboard.KEY_DOWN:
            print("\nESC key pressed. Stopping script...")
            keyboard.unhook_all()
            os._exit(0)  # Force exit the program

    def start_monitoring(self):
        """Starts the keyboard listener and waits for keywords."""
        print("--- Text Replacer is now active ---")
        print("Type a keyword followed by a SPACE to trigger a replacement.")
        print("Press ESC to exit.")
        
        # Hook the keyboard events
        keyboard.hook(self.on_key_event)
        keyboard.hook(self.stop_listener)
        
        # Keep the script running
        keyboard.wait('esc')  # Wait specifically for the ESC key to exit

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