# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

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
