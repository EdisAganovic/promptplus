# Changelog

All notable changes to PromptPlus will be documented in this file.

## [Unreleased] - Electron desktop migration

### Changed
- Replaced the PyQt desktop window and Quick Search with Electron windows and a system tray.
- Moved keyboard replacement to a standalone Python backend launched by Electron.
- Registered Quick Search through Electron's native global shortcut API, which reports shortcut collisions.
- Windows builds now package a Qt-free Python backend inside the Electron application.
- Windows distribution is a single installer EXE containing Electron and the Python backend.

## [Unreleased] - 2026-09-23

### Changed
- Windows builds now clear PyInstaller's cache and leave native DLLs uncompressed to reduce packaging-related startup failures.
- Prompt saves and imports now replace the JSON file atomically, so the text replacer does not read a partially written file.
- Quick Search uses `Ctrl+Alt+P` in both launchers. The shortcut no longer suppresses physical key events and triggers when the final shortcut key is released.
- Keyboard callbacks open Quick Search on the Qt UI thread. Shutdown removes only PromptPlus's own keyboard registrations.

### Fixed
- Imports reject JSON that is not a prompt object or contains invalid prompt content.
- Deleting or replacing the prompt file updates the text replacer's in-memory prompts.
- Paste cleanup no longer sends key-release events for keys the user may be holding.
- macOS paste cleanup no longer references an undefined key list.

## [0.5] - 2026-05-02

### Added
- **Thread-Safe UI Bridge** - Implemented `QuickSearchManager` using `pyqtSignal` to safely trigger UI actions from background threads, eliminating potential crashes during global hotkey activation.
- **Enhanced Quick Search** - Added the `Ctrl+Alt+P` global shortcut.
- **Improved Focus Management** - Added micro-delays using `QTimer` to ensure the Quick Search input field consistently gains focus after the window appears.
- **Suppress Qt Logging** - Disabled redundant QPA console warnings for a cleaner terminal output.

### Changed
- **Parallel Startup Optimization** - Refactored `main.py` to initialize the text replacer thread and GUI window in parallel, significantly reducing perceived startup time.
- **O(1) Trigger Lookups** - Optimized the replacement engine with a keyword length cache and hash map matching, drastically reducing CPU usage during typing.
- **Robust Path Handling** - Improved `utils.py` to correctly handle data storage in `AppData/Local` when running as a compiled executable, ensuring persistence across updates.
- **Enhanced Paste Reliability** - Improved clipboard timing around prompt insertion.
- **Performance Polishing** - Throttled file modification checks to once every 2 seconds to minimize disk I/O.

### Fixed
- **UI Thread Access Errors** - Resolved intermittent crashes when opening the Quick Search window from a background listener.
- **Clipboard Restoration Race Condition** - Increased restoration delays to ensure the system clipboard is correctly restored after pasting a prompt.
- **Data Corruption Guards** - Added retry logic and file locking for settings storage to prevent JSON corruption during simultaneous access.

## [0.4] - 2026-03-05

### Added
- **Quick Search Window** - Global hotkey (`Ctrl+Alt+P`) to quickly search and paste prompts into any application.
- **Dynamic Port Discovery** - Automatically finds an available port (starting from 8080) if the default port is already in use.
- **Robust Persistence** - Added file locking and retry logic to both prompt and settings storage to prevent data corruption.
- **Keyboard Hook Safeguards** - Graceful handling and logging for keyboard monitoring permission failures.

### Changed
- **Optimized Dashboard Layout** - Relocated the "+ Dodaj" button next to the search bar to improve workflow speed.
- **Alignments & Margins** - Standardized Bootstrap container hierarchy to fix right-side alignment mismatches.
- **Quick Search UX** - Added auto-selection, single-line results preview, and enhanced keyboard navigation (Arrows/Enter).

### Fixed
- **Text Replacement Leftover Character** - Fixed an issue where the first character of the trigger was not deleted by adding brief delays and increasing the backspace interval to give the OS time to process keys.
- **Quick Search Thread Safety** - Implemented `QuickSearchManager` to safely marshal UI calls from background threads.
- **Dashboard Right-Edge Gap** - Removed nested `container-fluid` discrepancies to ensure pixel-perfect vertical alignment.
- **Pyperclip Reliability** - Added error guards and timing delays to ensure clipboard-to-paste operations are stable across slow systems.

## [0.3] - 2026-03-04

### Added
- **Performance Optimizations** - Multiple improvements for smoother operation on slow CPUs
- **Thread-Safe Text Replacement** - Fixed race conditions in keyboard hook handling
- **Start Minimized Support** - `--minimize` flag now works correctly to start hidden in tray

### Changed
- **Removed Background Animations** - Eliminated cursor-following glow effects for better performance
- **Optimized Event Filter** - Replaced O(n) parent traversal with O(1) window check
- **Cursor Update Throttling** - Only updates cursor after 3px movement threshold
- **Keyword Caching** - Sorted keywords cached to avoid re-sorting on every keypress
- **Reduced File I/O** - File modification checks reduced from 10x/sec to once per 2 seconds
- **Faster Server Startup** - Exponential backoff for server health checks

### Fixed
- **Event Filter Memory Leak** - Properly remove event filter on window close
- **Keyword Collision on Edit** - Prevents silently overwriting existing prompts when renaming
- **Import Error Handling** - Invalid JSON now shows error instead of redirecting
- **Cursor Flicker on Maximize** - Reset cursor position cache when window state changes
- **Thread-Unsafe Buffer Access** - Added proper locking for `current_buffer` modifications
- **Dark Mode Form Text Visibility** - Added proper `.form-text` styling for dark theme

### Removed
- **Cursor-Tracking JavaScript** - Removed mouse position tracking from frontend
- **Blob Animation CSS Variables** - Cleaned up unused `--bg-glow`, `--blob-*` variables
- **Body Transition Effects** - Removed `transition` on body to prevent repaints on theme switch
- **Backdrop Filter Blur** - Removed expensive glassmorphism effects on cards and modals

## [0.2] - 2026-02-05

### Added
- **Interactive Background Animations** - Cursor-following glow effect and floating blobs for a modern, premium feel
- **Theme-Aware UI** - Toolbar and search box now adapt colors to match Light/Dark theme
- **System Tray Integration** - Minimize to tray, restore on click
- **Start with Windows** - Option to launch minimized on Windows startup
- **Centralized Version Number** - Single `VERSION` constant in `app/utils.py` for easier updates
- **Missing `/update_theme` API Route** - Theme changes now persist correctly

### Changed
- **Performance Optimized Animations** - Uses `requestAnimationFrame` and `will-change: transform` for GPU-accelerated rendering
- **Improved Search Box Visibility** - Solid background with high-contrast text for better readability

### Fixed
- **Syntax Error in `api.py`** - Resolved a broken return statement outside of a function
- **Toolbar Theme Switching** - Added explicit CSS selectors to ensure navbar background updates on theme toggle

## [0.1] - Initial Release

### Added
- Text replacement functionality with `:keyword` triggers
- Prompt management (add, edit, delete)
- Tag-based filtering and search
- Import/Export prompts as JSON
- Light/Dark theme support
