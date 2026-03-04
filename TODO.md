# PromptPlus - Feature Ideas / TODO

## 🐛 Bug Fixes

- [ ] **Theme Sync Between Web UI and Qt Window** - When theme is toggled in browser, Qt window's `apply_theme()` is not called
- [ ] **Keyword Collision on Edit** - Renaming `:test` to `:other` silently overwrites existing `:other` prompt
- [ ] **Import Error Handling** - Invalid JSON import should show error, not redirect
- [ ] **Event Filter Memory Leak** - Event filter not removed on window close
- [ ] **Cursor Position Cache** - `_last_cursor_pos` not reset on maximize, causes flicker

---

## ⚡ Performance Optimizations

### Backend
- [ ] **In-Memory Prompt Caching** - Cache processed prompts in API between requests, invalidate on write
- [ ] **Faster Clipboard API** - Use native Windows clipboard via `ctypes` instead of pyperclip
- [ ] **Reduce Backspace Interval** - Change from 0.003s to 0.001s per character
- [ ] **File I/O Reduction** - Cache file mod time, reduce stat calls

### Frontend (Web UI)
- [ ] **Search Input Debouncing** - Add 150ms delay before filtering runs
- [ ] **Single Dynamic Modal** - Replace N edit modals with one reusable modal
- [ ] **Lazy Load Modals** - Only create modals when needed
- [ ] **HTTP Caching Headers** - Add cache headers for static assets (CSS, JS, favicon)

### Qt GUI
- [ ] **QWebEngine Disk Cache** - Enable persistent profile with cache directory
- [ ] **Loading Sequence Optimization** - Show window immediately, load server in background
- [ ] **Pre-initialize WebView** - Create browser widget in background before showing
- [ ] **Reduce Loading Animation** - Slower timer or remove entirely

### CSS/Styles
- [ ] **Remove Unused CSS Variables** - Clean up blob animation constants
- [ ] **Remove Body Transitions** - `transition: background-color 0.2s` causes repaints on theme switch
- [ ] **Minify CSS** - Reduce style.css file size

### Text Replacement Engine
- [ ] **Keyword Match Optimization** - Use Aho-Corasick algorithm for multi-pattern matching
- [ ] **Buffer Size Limit** - Reduce from 100 to 50 characters for faster checks
- [ ] **Skip Clipboard Restore** - Only restore if original content differs

---

## 🚀 Productivity Boosters

- [ ] **Prompt Variables/Placeholders** - Support `{name}` or `{{date}}` in prompts that get replaced with dynamic values or prompt the user for input when triggered.
- [ ] **Prompt Categories/Folders** - Organize prompts into collapsible folders (e.g., "Work", "Code", "Email Templates").
- [ ] **Favorites/Pinned Prompts** - Star frequently used prompts to keep them at the top.
- [ ] **Usage Statistics** - Track which prompts are used most often, with a "Recently Used" section.

---

## ⚡ Power User Features

- [ ] **Keyboard Shortcuts** - Global hotkey (e.g., `Ctrl+Shift+P`) to open a quick-search popup for prompts without switching windows.
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
- [ ] **Remove Deprecated Code** - Clean up old `check_for_replacement()` method

---

## 📦 Build & Distribution

- [ ] **Auto-Update Checker** - Check for new versions on startup
- [ ] **Installer Improvements** - Add option to create desktop shortcut
- [ ] **Portable Version** - Single .exe that doesn't require installation
- [ ] **Code Signing** - Sign executable to avoid Windows SmartScreen warnings
- [ ] **Reduce Bundle Size** - Further exclude unused dependencies

---

## 🔒 Security

- [ ] **Input Sanitization** - Sanitize user input in prompts to prevent XSS
- [ ] **File Permission Checks** - Verify prompts.json permissions on startup
- [ ] **Secure Clipboard** - Clear sensitive data from clipboard after use
- [ ] **Registry Key Validation** - Validate registry paths for start-on-boot

---

*Last updated: March 2026*
