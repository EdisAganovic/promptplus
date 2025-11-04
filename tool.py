import json
import os
import time
import re
from pynput import keyboard
from pynput.keyboard import Key, Listener
import pyautogui
from typing import Dict
import pyperclip

# Global listener to allow stopping
listener = None

# File to store prompts
PROMPTS_FILE = "prompts.json"

class RealtimeTextReplacer:
    def __init__(self):
        self.prompts = self.load_prompts()
        self.current_buffer = ""
        self.max_keyword_length = max(len(k) for k in self.prompts.keys()) if self.prompts else 20
        self.is_replacing = False  # Flag to prevent recursion

    def load_prompts(self) -> Dict[str, str]:
        """Load prompts from a JSON file."""
        if os.path.exists(PROMPTS_FILE):
            with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_prompts(self, prompts: Dict[str, str]) -> None:
        """Save prompts to a JSON file."""
        with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, ensure_ascii=False, indent=2)

    def on_press(self, key):
        """Handle key press events."""
        # If a replacement is in progress, ignore new key presses
        if self.is_replacing:
            return

        try:
            if hasattr(key, 'char') and key.char is not None:
                self.current_buffer += key.char
            elif key == Key.space:
                self.current_buffer += ' '
            # Reset buffer on enter or tab for cleaner matching
            elif key in [Key.enter, Key.tab]:
                self.current_buffer = ""
            elif key == Key.backspace:
                if self.current_buffer:
                    self.current_buffer = self.current_buffer[:-1]
            
            # For debugging: print the current buffer
            # print(f"Buffer: '{self.current_buffer}'")

            # Keep the buffer manageable
            if len(self.current_buffer) > 100:
                self.current_buffer = self.current_buffer[-100:]

            self.check_for_replacement()

        except AttributeError:
            # Special keys (ctrl, alt, etc.) are ignored
            pass

    def check_for_replacement(self):
        """Check if buffer ends with a keyword and perform replacement if found."""
        if self.is_replacing:
            return

        # Sort keywords by length in descending order to match longer keywords first
        sorted_keywords = sorted(self.prompts.keys(), key=len, reverse=True)
        
        for keyword in sorted_keywords:
            if self.current_buffer.endswith(keyword):
                print(f"--- Match Found! Keyword: '{keyword}' ---")
                self.perform_replacement(keyword)
                return  # Only replace one keyword at a time

    def perform_replacement(self, keyword):
        """Perform the actual replacement in the active application."""
        self.is_replacing = True  # Set replacement flag
        
        replacement_text = self.prompts[keyword]
        
        # 1. Backspace the keyword to delete it
        print(f"Deleting keyword '{keyword}' by pressing backspace {len(keyword)} times.")
        for _ in range(len(keyword)):
            pyautogui.press('backspace')
            time.sleep(0.01) # Small delay for each backspace

        # 2. Type the replacement text
        print(f"Typing replacement text...")
        pyautogui.typewrite(replacement_text, interval=0.01)

        # Reset the buffer
        self.current_buffer = ""
        
        print(f"--- Replacement Complete for '{keyword}' ---")
        self.is_replacing = False # Unset replacement flag

    def start_monitoring(self):
        """Start the keyboard monitoring."""
        print("Monitoring started. Type your keywords to trigger replacement.")
        print("Press ESC to exit.")
        
        global listener
        listener = Listener(on_press=self.on_press, on_release=self.on_release)
        listener.start()
        listener.join()
    
    def on_release(self, key):
        """Handle key release events."""
        if key == Key.esc:
            print("\nStopping script...")
            return False  # Stop the listener

def main():
    # Example of how to add a prompt before starting
    replacer = RealtimeTextReplacer()
    
    # Clear existing prompts if you want to start fresh
    # replacer.save_prompts({}) 
    
    # Add some example prompts
    # replacer.add_prompt("@email", "my.email@example.com")
    # replacer.add_prompt("@sig", "Best regards,\nJohn Doe")

    print("Script is active...")
    replacer.start_monitoring()

if __name__ == "__main__":
    main()