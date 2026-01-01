# AGENTS.md

## Headless Execution

To run this application in a headless environment, you must set the `QT_QPA_PLATFORM` environment variable to `offscreen`.

Example:
```bash
export QT_QPA_PLATFORM=offscreen
python main.py
```

This will run the application without a graphical interface, which is useful for testing and other automated tasks.
