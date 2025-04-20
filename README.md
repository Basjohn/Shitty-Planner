# Shitty Life Planner

A DPI-aware, scalable, and clean Python desktop application for basic life planning. Tasks are organized into categories, and all data is saved locally in a simple SQLite database. UI is inspired by a retro tabbed planner.

## Features
- Editable categories and tasks
- Tasks grouped under categories
- Add/remove/rename categories and tasks
- Editable, scrollable task content
- All data saved in a local SQLite database
- DPI-aware, resizable, and clean UI (PyQt6)
- Transparent window borders (where supported)
- Save button with silent popup

## Getting Started

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   python main.py
   ```

All data is stored in `database.db` in the same folder as the executable/script.

## Project Structure
- `main.py`: Main application code
- `database.db`: Local SQLite database
- `requirements.txt`: Python dependencies
- `icons/save.svg`: Save icon

## Settings
Settings (window size, etc) will be stored in `settings.json` in the same folder.

---

**Note:** The UI is designed for easy extension and future feature additions.
