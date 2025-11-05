import subprocess
import sys
import signal
import os
import time

def run_ui():
    """Run the UI server."""
    subprocess.run([sys.executable, "-m", "uvicorn", "ui:app", "--host", "127.0.0.1", "--port", "8000"])

def run_tool():
    """Run the text replacement tool."""
    subprocess.run([sys.executable, "tool.py"])

if __name__ == "__main__":
    print("Starting GPT Plus system...")
    print("Starting UI server on http://127.0.0.1:8000")
    print("Starting text replacement tool")
    print("Press Ctrl+C to stop the system")
    
    # Start both processes
    ui_process = subprocess.Popen([sys.executable, "-m", "uvicorn", "ui:app", "--host", "127.0.0.1", "--port", "8000"])
    tool_process = subprocess.Popen([sys.executable, "tool.py"])
    
    def signal_handler(signum, frame):
        print("\nShutting down GPT Plus system...")
        ui_process.terminate()
        tool_process.terminate()
        ui_process.wait()
        tool_process.wait()
        sys.exit(0)
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Wait for both processes to finish
        ui_process.wait()
        tool_process.wait()
    except KeyboardInterrupt:
        signal_handler(None, None)