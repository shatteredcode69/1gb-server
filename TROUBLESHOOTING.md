# Troubleshooting

## Error: "Fatal error in launcher: Unable to create process"

**Cause:** Virtual environment is corrupted

**Solution:**
1. Delete venv folder
2. Recreate it: `python -m venv venv`
3. Activate: `venv\Scripts\activate.bat`
4. Install: `pip install -r app\requirements.txt`

## Quick Fix
Run: `fix-venv.bat`
