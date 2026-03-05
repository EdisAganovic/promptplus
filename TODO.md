# PromptPlus - Feature Ideas / TODO

## ✅ Completed / Fixed

- [x] **Event Filter Memory Leak** - Fixed: Event filter removed on window close
- [x] **Cursor Position Cache** - Fixed: `_last_cursor_pos` reset on maximize/resize
- [x] **Keyword Collision on Edit** - Fixed: API now checks for existing keywords before overwrite
- [x] **Import Error Handling** - Fixed: Invalid JSON shows error message
- [x] **File I/O Reduction** - Fixed: File mod time cached, checks every 2 seconds
- [x] **Prompt Caching** - Fixed: Keywords sorted and cached, invalidated on change
- [x] **Remove Unused Packages** - Removed: streamlit, pynput, json5 from requirements
- [x] **UPX Compression** - Added to build.py for 50-70% smaller executable
- [x] **Remove Body Transitions** - Removed navbar transition to prevent repaints on theme switch
- [x] **Remove Unused CSS Variables** - Removed: --navbar-bg, --glass-blur, --glass-border

---

## 🐛 Bug Fixes

- [x] **Theme Sync Between Web UI and Qt Window** - When theme is toggled in browser, Qt window's `apply_theme()` is not called (requires WebSocket or polling)

---

## ⚡ Performance Optimizations

### Backend
- [x] **Remove Info Messages** - Removed print statements and set uvicorn log_level="error"
- [ ] **Faster Clipboard API** - Use native Windows clipboard via `ctypes` instead of pyperclip
- [ ] **Reduce Backspace Interval** - Change from 0.003s to 0.001s per character
- [ ] **Skip Clipboard Restore** - Only restore if original content differs

### Frontend (Web UI)
- [x] **Single Dynamic Modal** - Replaced N edit modals with one reusable modal
- [x] **Lazy Load Modals** - Only create modals when needed (reduced from N+4 to 5 modals)
- [x] **Search Input Debouncing** - Add 150ms delay before filtering runs

### CSS/Styles
- [ ] **Remove Unused CSS Variables** - Clean up blob animation constants
- [ ] **Remove Body Transitions** - `transition: background-color 0.2s` causes repaints on theme switch
- [ ] **Minify CSS** - Reduce style.css file size

### Text Replacement Engine
- [x] **Buffer Size Limit** - Reduced from 100 to 50 characters for faster checks
- [ ] **Keyword Match Optimization** - Use Aho-Corasick algorithm for multi-pattern matching

---

## 🚀 Productivity Boosters

- [ ] **Prompt Variables/Placeholders** - Support `{name}` or `{{date}}` in prompts that get replaced with dynamic values or prompt the user for input when triggered.
- [ ] **Prompt Categories/Folders** - Organize prompts into collapsible folders (e.g., "Work", "Code", "Email Templates").
- [ ] **Favorites/Pinned Prompts** - Star frequently used prompts to keep them at the top.
- [ ] **Usage Statistics** - Track which prompts are used most often, with a "Recently Used" section.

---

## ⚡ Power User Features

- [x] **Keyboard Shortcuts** - Global hotkey (e.g., `Ctrl+Shift+P`) to open a quick-search popup for prompts without switching windows.
- [ ] **Chained Prompts** - Link multiple prompts together (e.g., `:intro` followed by `:signature`).
- [ ] **Clipboard History Integration** - Optionally append/prepend clipboard content to prompts.
- [ ] **Markdown Preview** - For longer prompts, show a rendered preview.
- [ ] **Rich Text Support** - Allow formatted text (bold, italic, lists) in prompts.
- [ ] **Prompt Export/Share** - Export individual prompts as shareable snippets.
- [ ] **Smart Triggers** - Context-aware triggers based on active application.

---

## 🎨 UI/UX Enhancements

- [ ] **Prompt Templates** - Pre-built starter prompts users can import (e.g., "Email Templates Pack", "Code Review Prompts").
- [ ] **Drag & Drop Reordering** - Rearrange prompts by dragging cards.
- [ ] **Dark/Light/Auto Theme** - Add system theme detection option.
- [ ] **Customizable Window Size** - Remember last window size and position.
- [ ] **Compact Mode** - Smaller card layout for users with many prompts.
- [ ] **Search Highlighting** - Highlight matched search terms in results.
- [ ] **Undo Delete** - Toast with "Undo" button after deleting a prompt.
- [ ] **Empty State Improvements** - Add sample prompts to get started quickly.

---

## 🔄 Sync & Backup

- [ ] **Cloud Sync** - Sync prompts across devices via Google Drive, Dropbox, or a simple JSON link.
- [ ] **Auto-Backup** - Automatically save versioned backups of `prompts.json`.
- [ ] **Import/Export Individual Prompts** - Export single prompts as JSON files.
- [ ] **Merge on Import** - Option to merge imported prompts instead of replacing all.

---

## 🏗️ Code Quality

- [ ] **Add Type Hints** - Add Python type hints to all functions
- [ ] **Unit Tests** - Add pytest tests for replacer logic and API endpoints
- [ ] **Integration Tests** - Test full replacement flow with mock keyboard
- [ ] **Error Reporting** - Add crash reporting with user permission
- [ ] **Logging Improvements** - Structured logging with file rotation
- [ ] **Configuration Validation** - Validate settings.json schema on load
- [ ] **Remove Deprecated Code** - Clean up old `check_for_replacement()` and `perform_replacement()` methods

---

## 📦 Build & Distribution

- [ ] **Auto-Update Checker** - Check for new versions on startup
- [ ] **Installer Improvements** - Add option to create desktop shortcut during install
- [ ] **Portable Version** - Single .exe that doesn't require installation
- [ ] **Code Signing** - Sign executable to avoid Windows SmartScreen warnings

---

## 🔒 Security

- [ ] **Input Sanitization** - Sanitize user input in prompts to prevent XSS
- [ ] **File Permission Checks** - Verify prompts.json permissions on startup
- [ ] **Secure Clipboard** - Clear sensitive data from clipboard after use
- [ ] **Registry Key Validation** - Validate registry paths for start-on-boot

---

*Last updated: March 5, 2026*
