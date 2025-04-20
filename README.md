# Shitty Planner

A DPI-aware, scalable, and clean Python desktop application for basic planning. Tasks are organized into categories, and all data is saved locally in a simple SQLite database. UI is inspired by a retro tabbed planner. Useful for both planning tasks and notekeeping.

## Features
- Ability to false positive Windows Defender without fail
- Editable categories and tasks
- Tasks grouped under categories
- Add/remove/rename categories and tasks
- Editable, scrollable task content
- All data saved in a local SQLite database
- DPI-aware, resizable, and clean UI (PyQt6)
- Transparent window borders (where supported)
- Save button with silent popup

All data is stored in `database.db` in the same folder as the executable/script.

## Project Structure
- `main.py`: Main application code
- `database.db`: Local SQLite database
- `requirements.txt`: Python dependencies
- `icons/save.svg`: Save icon

## Settings
Settings (window size, etc) will be stored in `settings.json` in the same folder.

---

## USAGE
- Either run the Exe or if (likely) Windows Defender falsely flags this like the insecure bitch it is then make sure you have PyQt6
and simply run main.py
- Supports Rich Text in Task/Note sections. Ctrl+B for Bold, Crtl+U for underline.
- Great for people with brains that are turning into jello like mine, fully portable unlike said brains.

**Note:** The UI is designed for easy extension and future feature additions.
