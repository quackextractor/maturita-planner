# Maturita Planner

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.3.6-blue.svg)](https://github.com/quackextractor/maturita-planner)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A visual drag-and-drop daily planner designed specifically for managing markdown-based study schedules.

## Features
* **Markdown Parsing**: Automatically reads your study blocks and daily routine slots.
* **Drag and Drop**: Visually drag tasks into your daily routine. Tasks float cleanly over the UI for precise placement.
* **Progress Tracking**: Tick off completed tasks and save your progress visually. State persists across application restarts.
* **Autosave & Manual Saving**: Automatically saves your progress by default, with an option to toggle autosave off and save manually.
* **Plan Preservation**: Keeps your original plan intact in an isolated internal folder, preventing accidental data loss if you modify external files.
* **Daily and Full Resets**: Effortlessly revert a single day or the entire plan back to its original imported state.
* **Sync Compatibility**: Directly modifies the active markdown file within the data directory, natively supporting synchronization tools like SyncThing.
* **Word Wrap & Formatting**: Supports markdown bold styling (**text**) and dynamic word wrapping for longer task descriptions.

## Example Configuration Files

To start using the app, you need two markdown files: `plan.md` and `routine.md`. Ensure your files follow these structural examples.

### 1. `plan.md` Example
This file dictates your study blocks. It must contain days marked with bold headers, followed by a markdown list of tasks.

```markdown
### Maturita Study Plan

**Day 1: Mathematics**
* [ ] **Linear Algebra** Review matrices and vectors.
* [ ] **Calculus** Practice derivatives.
* [x] **Geometry** Completed yesterday.

**Day 2: Physics**
* [ ] **Kinematics** Review motion equations.
* [ ] **Thermodynamics**
```

### 2. `routine.md` Example
This file establishes your daily timetable. The application scans for bolded time slots that include "Study Block" in the description.

```markdown
### Daily Schedule

* **08:00 to 09:30** Study Block 1
* **09:30 to 10:00** Morning Break
* **10:00 to 11:30** Study Block 2
* **11:30 to 13:00** Lunch
* **13:00 to 14:30** Study Block 3
```

## Usage
Run the application:
```bash
python main.py
```
On first launch, the app will ask you to drag and drop your `plan.md` and `routine.md` into the setup window. The app will generate a `data/` folder to save your daily progress without altering your original files.