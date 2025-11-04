import time
import sys

def method1_pyautogui():
    """Method 1: Using pyautogui.keyDown and keyUp"""
    print("Method 1: Using pyautogui.keyDown and keyUp")
    import pyautogui
    try:
        pyautogui.keyDown('ctrl')
        print("Holding CTRL for 5 seconds...")
        time.sleep(5)
        pyautogui.keyUp('ctrl')
        print("Released CTRL")
    except Exception as e:
        print(f"Error in Method 1: {e}")

def method2_win32api():
    """Method 2: Using win32api.keybd_event"""
    print("Method 2: Using win32api.keybd_event")
    import win32api
    import win32con
    try:
        # Press CTRL down (virtual key code 0x11)
        win32api.keybd_event(0x11, 0, 0, 0)
        print("Holding CTRL for 5 seconds...")
        time.sleep(5)
        # Release CTRL up
        win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)
        print("Released CTRL")
    except Exception as e:
        print(f"Error in Method 2: {e}")

def method3_keyboard():
    """Method 3: Using keyboard.press_and_release"""
    print("Method 3: Using keyboard.press_and_release")
    import keyboard
    try:
        keyboard.press('ctrl')
        print("Holding CTRL for 5 seconds...")
        time.sleep(5)
        keyboard.release('ctrl')
        print("Released CTRL")
    except Exception as e:
        print(f"Error in Method 3: {e}")

def method4_win32api_extended():
    """Method 4: Using win32api.keybd_event with scan codes"""
    print("Method 4: Using win32api.keybd_event with scan codes")
    import win32api
    import win32con
    try:
        # Press CTRL down (virtual key code 0x11, scan code 0x1D)
        win32api.keybd_event(0x11, 0x1D, 0, 0)  # CTRL down
        print("Holding CTRL for 5 seconds...")
        time.sleep(5)
        # Release CTRL up (virtual key code 0x11, scan code 0x1D)
        win32api.keybd_event(0x11, 0x1D, win32con.KEYEVENTF_KEYUP, 0)  # CTRL up
        print("Released CTRL")
    except Exception as e:
        print(f"Error in Method 4: {e}")

def method5_win32api_lobyte():
    """Method 5: Using win32api.keybd_event with proper flags"""
    print("Method 5: Using win32api.keybd_event with proper flags")
    import win32api
    import win32con
    try:
        # Press CTRL down using MapVirtualKey to get scan code
        scan_code = win32api.MapVirtualKey(0x11, 0)  # Convert virtual key to scan code
        win32api.keybd_event(0x11, scan_code, 0, 0)  # CTRL down
        print("Holding CTRL for 5 seconds...")
        time.sleep(5)
        # Release CTRL up
        win32api.keybd_event(0x11, scan_code, win32con.KEYEVENTF_KEYUP, 0)  # CTRL up
        print("Released CTRL")
    except Exception as e:
        print(f"Error in Method 5: {e}")

def method6_direct_input():
    """Method 6: Using SendInput from ctypes"""
    print("Method 6: Using SendInput from ctypes")
    from ctypes import windll, Structure, c_ushort, c_ulong, c_ulonglong, sizeof, pointer
    from ctypes.wintypes import DWORD, ULONG
    import sys

    # Define structures for INPUT and KEYBDINPUT
    class KEYBDINPUT(Structure):
        _fields_ = [
            ('wVk', c_ushort),
            ('wScan', c_ushort),
            ('dwFlags', c_ulong),
            ('time', c_ulong),
            ('dwExtraInfo', c_ulonglong if sys.maxsize > 2**32 else c_ulong)
        ]

    class INPUT_union(Structure):
        _fields_ = [('ki', KEYBDINPUT)]

    class INPUT(Structure):
        _fields_ = [('type', c_ulong), ('union', INPUT_union)]

    # Constants
    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    VK_CONTROL = 0x11

    try:
        # Create input structures for pressing CTRL
        ctrl_press = INPUT()
        ctrl_press.type = INPUT_KEYBOARD
        ctrl_press.union.ki.wVk = VK_CONTROL
        ctrl_press.union.ki.wScan = 0
        ctrl_press.union.ki.dwFlags = 0  # Key down
        ctrl_press.union.ki.time = 0
        ctrl_press.union.ki.dwExtraInfo = 0

        # Create input structures for releasing CTRL
        ctrl_release = INPUT()
        ctrl_release.type = INPUT_KEYBOARD
        ctrl_release.union.ki.wVk = VK_CONTROL
        ctrl_release.union.ki.wScan = 0
        ctrl_release.union.ki.dwFlags = KEYEVENTF_KEYUP
        ctrl_release.union.ki.time = 0
        ctrl_release.union.ki.dwExtraInfo = 0

        # Send the key press
        windll.user32.SendInput(1, pointer(ctrl_press), sizeof(INPUT))
        print("Holding CTRL for 5 seconds...")
        time.sleep(5)
        # Send the key release
        windll.user32.SendInput(1, pointer(ctrl_release), sizeof(INPUT))
        print("Released CTRL")
    except Exception as e:
        print(f"Error in Method 6: {e}")

if __name__ == "__main__":
    print("Testing 6 different methods to hold down CTRL for 5 seconds")
    print("="*60)
    
    # Test each method
    methods = [
        method1_pyautogui,
        method2_win32api,
        method3_keyboard,
        method4_win32api_extended,
        method5_win32api_lobyte,
        method6_direct_input
    ]
    
    for i, method in enumerate(methods, 1):
        print(f"\n--- Testing Method {i} ---")
        try:
            method()
            print(f"Method {i} completed")
        except Exception as e:
            print(f"Method {i} failed with error: {e}")
        
        # Wait before next method
        if i < len(methods):
            print("Waiting 2 seconds before next method...\n")
            time.sleep(2)
    
    print("\n" + "="*60)
    print("All methods tested!")