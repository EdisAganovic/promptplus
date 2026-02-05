# Changelog

All notable changes to PromptPlus will be documented in this file.

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
