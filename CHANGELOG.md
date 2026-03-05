# Changelog

All notable changes to PromptPlus will be documented in this file.

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
