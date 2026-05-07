# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

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