import psutil
import os
import sys
from tool import RealtimeTextReplacer

def check_existing_instances():
    """Check if there are already instances of this program running."""
    current_pid = os.getpid()
    current_process = psutil.Process(current_pid)
    
    try:
        current_exe = current_process.exe()
    except (psutil.AccessDenied, psutil.ZombieProcess):
        # Fallback to command line if we can't get the exe path
        try:
            current_exe = ' '.join(current_process.cmdline())
        except (psutil.AccessDenied, ValueError):
            # If everything fails, return False to allow the process to start
            return False, None
    
    # Get the base name of the current executable to compare with other processes
    current_basename = os.path.basename(current_exe).lower()
    
    for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
        try:
            # Check the executable path first
            proc_exe = proc.info['exe']
            if proc_exe:
                proc_basename = os.path.basename(proc_exe).lower()
                
                # Compare basenames to avoid path differences
                if (proc_basename == current_basename and 
                    proc.info['pid'] != current_pid and
                    proc.is_running()):
                    
                    print(f"Another instance of the program is already running (PID: {proc.info['pid']})")
                    return True, proc.info['pid']
            else:
                # If exe path is not available, try using command line
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline:
                        # Check if the command line contains the same executable
                        cmd_first = cmdline[0] if cmdline else ""
                        cmd_basename = os.path.basename(cmd_first).lower()
                        if (cmd_basename == current_basename and 
                            proc.info['pid'] != current_pid and
                            proc.is_running()):
                            
                            print(f"Another instance of the program is already running (PID: {proc.info['pid']})")
                            return True, proc.info['pid']
                except (psutil.AccessDenied, ValueError):
                    continue  # Skip if can't access command line
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False, None

def run_tool():
    """Run the text replacement tool."""
    # Check if there are already instances running
    is_running, existing_pid = check_existing_instances()
    if is_running:
        print(f"Another instance of the program is already running (PID: {existing_pid}).")
        print("Only one instance of GPTPlus should be running at a time.")
        sys.exit(0)  # Exit with code 0 to indicate normal behavior, not an error
        
    replacer = RealtimeTextReplacer()
    replacer.start_monitoring()

if __name__ == "__main__":
    run_tool()