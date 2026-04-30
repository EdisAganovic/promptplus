# PromptPlus - Real-time Prompt Replacer

## Description
A tool for managing prompts with keywords that are automatically replaced in real-time as you type in any application.

## Features
- Define prompts with keywords (e.g., :translate, :summarize)
- Automatic keyword replacement as you type in any application
- Manage prompts through a web interface (FastAPI)
- Compatibility with Gemini AI models
- Ability to set environment variables (API keys)
- Animated loading screen with "Loading..." text and dots when the application starts
- Borderless window design with buttons for minimization, maximization, and closing

## Usage
1. Start the application: `python ui.py`
2. The UI will open in a window (backend at `http://127.0.0.1:8080`)
3. Add your prompts with keywords
4. The text replacer automatically runs in the background

## Installation
```
uv pip install -r requirements.txt
```

## Running
```
python ui.py
```

## Configuration
- The application uses a `.env` file to store API keys and environment variables
- If a `.env` file does not exist, it will be automatically created with examples

## Notes
- The application must have permissions for keyboard monitoring and keypress simulation
- During replacement, the original clipboard content is saved and restored after replacement
- The application uses the `prompts.json` file to save prompts between sessions
- For the best experience, use keywords that will not appear accidentally in normal text
- The web interface uses FastAPI instead of Streamlit due to compilation issues into EXE