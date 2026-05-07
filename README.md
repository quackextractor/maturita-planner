# Maturita Planner

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.4.1-blue.svg)](https://github.com/quackextractor/maturita-planner)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A visual drag-and-drop daily planner designed specifically for managing markdown-based study schedules.

## Features
* **Smart Metadata Parsing**: Automatically parses nested details like difficulty, hours, and iterations out of your markdown and turns them into visual, colored UI badges. 
* **Subject Color-Coding**: Visually identifies the subject of your task (e.g., PV, DS, LIT) based on your headings and colors task borders appropriately so you can scan your schedule at a glance.
* **Markdown Parsing**: Automatically reads your study blocks and daily routine slots without destroying document context.
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
This file dictates your study blocks. It must contain days marked with bold headers, followed by a markdown list of tasks. Non-task text like totals or dates will be safely preserved. The application will use items inside parenthesis to generate colored badges.

```markdown
### Maturita Study Plan (May 07 - May 21, 2026)

**Day 1: Thursday, May 07**
* **PV 1:** Adresování a správa paměti (Hard, 12 iterací, 2.0h) - Focus: Theory and practical examples/code.
* **DS 1:** Relační databázové systémy (Medium, 6 iterací, 1.0h) - Focus: Theory and practical examples/code.
* **LIT 1:** W. Shakespeare: Hamlet (Easy, 7 iterací, 1.1h) - Focus: Author context and book plot/themes.
* *Total: 38 iterací (6.2 hours)*

**Day 2: Friday, May 08**
* **PV 2:** Algoritmizace - Grafy a prohledávání (Hard, 12 iterací, 2.0h) - Focus: Theory and practical examples/code.
```

### 2. `routine.md` Example
This file establishes your daily timetable. The application scans for bolded time slots that include "Study Block" in the description and visually pulls in that description.

```markdown
### Daily Routine Structure

* **06:30 to 07:00**: Wake up and eat breakfast.
* **07:00 to 09:00**: Study Block 1 (Topic 1).
* **09:00 to 09:30**: Break.
* **09:30 to 11:30**: Study Block 2 (Topic 2).
* **11:30 to 12:30**: Lunch break.
* **12:30 to 13:30**: 1 hour outside.
```

## Usage
Run the application:
```bash
python main.py
```
On first launch, the app will ask you to drag and drop your `plan.md` and `routine.md` into the setup window. The app will generate a `data/` folder to save your daily progress without altering your original files.