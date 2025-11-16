# Fix Flask Import Issues in VS Code

## Problem

VS Code shows Flask as unresolved import (red squiggly line) even though Flask is installed and working.

## Solution

### Quick Fix (Automatic)

I've created `.vscode/settings.json` with the correct Python interpreter path.

**Restart VS Code** and the Flask import errors should disappear.

### Manual Fix (if needed)

1. **Open Command Palette**: Press `Ctrl+Shift+P` (Windows) or `Cmd+Shift+P` (Mac)

2. **Select Python Interpreter**: Type "Python: Select Interpreter"

3. **Choose**: Select `Python 3.13.1 64-bit` at:
   ```
   C:\Users\nanda\AppData\Local\Programs\Python\Python313\python.exe
   ```

4. **Reload Window**: Press `Ctrl+Shift+P` and type "Developer: Reload Window"

## Verify Flask is Working

Run this to confirm Flask works:

```bash
py -c "from flask import Flask; print('Flask is working!')"
```

Expected output:
```
Flask is working!
```

## If Still Not Resolved

### Option 1: Install Flask in VS Code Terminal

1. Open VS Code terminal
2. Run:
   ```bash
   py -m pip install --upgrade Flask flask-cors python-dotenv
   ```

### Option 2: Create Virtual Environment

If you want to use a virtual environment:

```bash
# Create virtual environment
py -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

Then in VS Code:
1. Press `Ctrl+Shift+P`
2. Type "Python: Select Interpreter"
3. Choose the interpreter from `venv` folder

## Check Installation

```bash
py -m pip list | findstr -i flask
```

Should show:
```
Flask              3.1.2
flask-cors         4.0.0
```

## Why This Happens

VS Code uses Pylance (Python language server) to check imports. Sometimes it gets confused about which Python installation to use, especially if you have:
- Multiple Python versions
- Python from Microsoft Store
- Python from python.org
- Virtual environments

The `.vscode/settings.json` file tells VS Code exactly which Python to use.

## Files Created

- `.vscode/settings.json` - VS Code Python configuration

## Note

Flask **IS** installed and working correctly. This is purely a VS Code display issue. Your code will run fine even if VS Code shows the warning.

Test it:
```bash
py adaptive_music_backend.py
```

If the app starts, Flask is working! The red squiggly lines are just a VS Code configuration issue.
