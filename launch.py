#!/usr/bin/env python
"""
Simple launcher script for NBA Performance Predictor
This ensures the app runs with the correct Python interpreter
"""
import os
import sys
import subprocess

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the app
    app_path = os.path.join(script_dir, "app.py")
    
    # Path to Python in virtual environment
    if sys.platform == "win32":
        python_path = os.path.join(script_dir, "env", "Scripts", "python.exe")
    else:
        python_path = os.path.join(script_dir, "env", "bin", "python")
    
    # Check if virtual environment exists
    if not os.path.exists(python_path):
        print("ERROR: Virtual environment not found!")
        print(f"Expected Python at: {python_path}")
        print("\nPlease create a virtual environment first:")
        print("  python -m venv env")
        print("  .\\env\\Scripts\\activate  (Windows)")
        print("  pip install -r requirements.txt")
        return 1
    
    # Check if app exists
    if not os.path.exists(app_path):
        print(f"ERROR: app.py not found at {app_path}")
        return 1
    
    print("=" * 50)
    print("  NBA Performance Predictor")
    print("=" * 50)
    print()
    print("Starting Streamlit app...")
    print(f"Python: {python_path}")
    print(f"App: {app_path}")
    print()
    print("The app will open in your browser at:")
    print("  http://localhost:8501")
    print()
    print("Press Ctrl+C to stop the server")
    print()
    
    # Run streamlit
    try:
        subprocess.run([python_path, "-m", "streamlit", "run", app_path], 
                      cwd=script_dir,
                      check=True)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Streamlit failed to start (exit code {e.returncode})")
        return e.returncode
    except FileNotFoundError:
        print(f"\nERROR: Could not find Python at {python_path}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())


