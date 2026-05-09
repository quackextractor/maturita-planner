# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

## [1.5.2] - 2026-05-09
### Fixed
* Date Parsing Robustness: Updated the parsing engine in `src/planner.py` to use a more resilient extraction logic that explicitly ignores "Day X" keywords. This ensures the application correctly identifies the calendar date even when "Day" appears before the month in headers.
* Library Widget Caching: Implemented isolated UI caches for the Library view. The application now builds library task widgets only once and updates their internal state (completion, tags, text) dynamically, significantly reducing CPU usage and eliminating UI flickering when switching between views or applying filters.

### Changed
* Feature Documentation: Refined the "Intelligent Date Matching" description in `README.md` to better reflect the automatic rollover and day-detection capabilities.

## [1.5.1] - 2026-05-09
### Changed
* Library Performance: Significantly improved the loading and searching speed in the Library view. Implemented a 300ms input debounce and a widget recycling system that toggles visibility instead of destroying and recreating UI elements on every keystroke.

### Fixed
* Rollover Synchronization: Fixed a bug where the UI and the data layer calculated the current day independently. The application now uses a centralized calculation to ensure the UI correctly focuses on the day receiving rolled-over tasks.
* Date Parsing Robustness: Resolved an issue where task rollover could silently fail if system language differences prevented datetime parsing. The engine now safely falls back to extracting the day sequence integer directly from the markdown header (e.g., "Day 1") to guarantee chronological forwarding.

## [1.5.0] - 2026-05-09
### Added
* Library View: A comprehensive new screen to search, filter, and review all tasks across all days.
* Multi-Selection Engine: Support for standard click, Ctrl-Click, and Shift-Click to select multiple tasks simultaneously.
* Mass Actions: Checkbox toggling and drag-and-drop operations now apply to all selected tasks concurrently.
* Day Migration: Introduce a "Move to Day" action bar for selected tasks to shift them permanently between days.
* Intelligent Date Rollover: The app now extracts the core year and automatically moves incomplete tasks from past days to the current day.
* Auto-Day Focus: The application auto-detects `today` and immediately opens the relevant day on startup.

### Changed
* Abstract Syntax Tree Parser: Completely rewrote the markdown reading and writing engine to preserve document integrity when tasks migrate across sections.
* Top Navigation: Renamed "Open Data Folder" to "Data" to optimize horizontal spacing.
* Event Binding Architecture: Rebuilt the drag manager to smoothly distinguish between clicking and dragging.

## [1.4.3] - 2026-05-09
### Fixed
* Executable Data Persistence: Resolved an issue where the compiled PyInstaller application would lose saved progress and state upon closing.
* Path Resolution: Replaced the temporary `sys._MEIPASS` extraction path with `sys.executable` to ensure the internal data folder is generated and read safely alongside the application binary.

## [1.4.2] - 2026-05-07
### Added
* Hybrid Color-Coding: Reintroduced hand-picked, premium colors for standard subjects (PV, DS, LIT, CJ) and specific metadata keywords (Hard, Medium, Easy, h, iterac) for better visual hierarchy.
* Improved Deterministic Generator: The dynamic color engine now snaps to a predefined list of `safe_hues` (15-degree spacing) to ensure generated colors for custom tags are visually distinct and never clash with the primary palette.
* Task Syntax Documentation: Added a detailed breakdown of task syntax and parsing rules to the README.

## [1.4.1] - 2026-05-07
### Added
* Deterministic Dynamic Coloring: Subjects and badges now receive consistent, aesthetically pleasing colors based on their text content, eliminating the need for hardcoded color mappings.
* New `get_deterministic_colors` utility to generate stable HLS-based color pairs for light and dark modes.

## [1.4.0] - 2026-05-07
### Added
* Smart Metadata Parsing: Automatically extracts metadata from parentheses (e.g., difficulty, hours, iterations) and displays them as colored badges in the UI.
* Subject Color-Coding: Task borders are now color-coded based on the detected subject (PV, DS, LIT, ČJ/CJ) for better visual scanning.
* Enhanced Task Layout: Redesigned task widgets with thicker, subject-aware borders and better internal spacing.

### Changed
* UI Aesthetics: Improved the overall look of task blocks with subject-specific highlights and badge systems.
* Draggable Elements: Ensured all parts of the task widget, including badges and nested frames, are draggable targets.

### Fixed
* Task Text Display: Tasks now show cleaner text by stripping metadata badges from the main description label.

## [1.3.7] - 2026-05-07
### Fixed
* Version Script Encoding: Fixed a `UnicodeDecodeError` in `update_version.py` by explicitly specifying UTF-8 encoding when reading `README.md` and `CHANGELOG.md`.

## [1.3.6] - 2026-05-07
### Fixed
* Autosave Indicator: The "Last saved" timestamp now correctly updates in the UI immediately after an autosave event triggered by task completion or drag-and-drop operations.

## [1.3.5] - 2026-05-07
### Fixed
* Scrollbar Visibility: Fixed an issue where the scrollbar was missing when needed by using the correct internal frame height check in `AutoScrollableFrame`.
* Canvas Attribute Error: Resolved `AttributeError` by replacing the nonexistent `_parent_canvas_window` with `_create_window_id` when forcing width synchronization.

## [1.3.4] - 2026-05-07
### Fixed
* Target Identification: Destroying the floating proxy widget prior to evaluating the drop location correctly registers the target slot, restoring drag-and-drop functionality.
* Unnecessary Scrollbars: Restored standard framework bindings to the scrollable frame alongside active custom width resizing logic, fixing false-positive scrollbars.
* Container Expansion: Activated "stretch=always" in the PanedWindow columns so both columns correctly utilize the total application width, solving the "half-space" look.

## [1.3.3] - 2026-05-07
### Fixed
* Robust Dragging: Replaced the experimental reparenting logic with a floating proxy widget. This ensures tasks can "escape" their containers and float over the entire UI without being clipped or having weird offsets.
* Layout Expansion: Adjusted the main paned window to ensure columns utilize the full available width, eliminating the "half-empty" look on larger screens.
* Permanent Squishing Fix: Implemented active width synchronization between the scrollable canvas and its internal frame, ensuring tasks always fill the column width.

## [1.3.2] - 2026-05-07
### Fixed
* Drag Visibility: Tasks now "float" above all UI elements when being dragged, preventing clipping by scrollable frame boundaries.
* Layout Stability: Forced internal width synchronization in scrollable frames to permanently eliminate task "squishing" on resize.
* Drag-and-Drop Reliability: Refined event interception to absolutely prevent text selection conflicts during task movement.

## [1.3.0] - 2026-05-07
### Added
* Auto-hiding scrollbars: Sidebar and Main view scrollbars now only appear when content exceeds the visible window height.
* Drag Feedback: Mouse cursor now changes to a "hand" pointer during task dragging for improved interaction clarity.
* Unit Testing: Introduced automated testing suite for core logic to ensure stability.

### Changed
* Flash-Free UI Updates: Task completion and drag-and-drop operations now perform targeted updates instead of full UI regeneration.
* Enhanced UI Separator: The adjustable divider between columns is now wider (8px) with a 3D relief and specialized hover cursor.

## [1.2.1] - 2026-05-07
### Added
* Official application icon for both runtime window and compiled executables.
* Dynamic height calculation for task blocks to better accommodate long descriptions.

### Fixed
* UI Corner Artifacts: Added theme-matching background to the main PanedWindow to hide rounded corner bleeding.
* Drag Lag: Disabled opaque resizing for the main PanedWindow to ensure smooth UI performance during sidebar adjustment.
* DragManager TypeError: Resolved a potential `TypeError` when clicking navigation buttons rapidly during UI regeneration.

## [1.2.0] - 2026-05-07
### Added
* Save Status Indicator in the top navigation bar showing the last successful save time.
* Open Data Folder button to quickly access the internal plan and routine storage.
* Intuitive Day Navigation with Previous (<) and Next (>) buttons.
* Word Wrap support for task descriptions using CTkTextbox.
* Markdown Bold Styling support (e.g., **important**) within task descriptions.

### Changed
* Improved Task Dragging: The entire task surface (excluding the checkbox) is now draggable, removing the need for a dedicated handle.

### Fixed
* Ticked Block Moving Bug: Fixed an issue where ticking a task's checkbox would unintentionally reset its assigned routine slot.
* CTkTextbox Scaling Crash: Resolved an `AttributeError` when applying bold fonts in task descriptions by bypassing `CustomTkinter` scaling restrictions for specific text tags.

## [1.1.0] - 2026-05-07
### Changed
* Overhauled architecture to maintain two versions of the plan: the preserved original and the active version.
* The application now reads and writes state directly to `active_plan.md`, natively supporting external tools like SyncThing.
* Added a dedicated drag handle `[::]` to tasks to eliminate conflicts with the completion checkbox.
* Added visual confirmation text during the initial drag-and-drop setup phase.
* Added Plan Reset and Major Deletion features.
* Removed the obsolete Export Day functionality.

## [1.0.1] - 2026-05-07
### Changed
* Overhauled file import logic to copy `plan.md` and `routine.md` into an isolated internal `data/` directory upon drag-and-drop. This prevents the app from breaking if the user deletes the original external files.
* Modified the drag-and-drop functionality to use `tkinterdnd2` to allow files to be dropped directly from the operating system into the application window.
* Added a welcome screen that displays when no active configuration files are found in the data directory.
* Added an "Export Day" button to compile completed and unassigned tasks back into a markdown file.

## [1.0.0] - 2026-05-07
### Added
* Initial release of the Maturita Planner utility.
* Drag and drop functionality for assigning study blocks to daily routine slots.
* Markdown import and export for study plans and daily routines.
* State persistence to track completed (ticked) tasks without deleting them.
* Reset day functionality to revert to the original markdown plan.