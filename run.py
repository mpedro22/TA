#!/usr/bin/env python3

import subprocess
import sys
import os

def main():
    """Run the Streamlit application"""
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_file = os.path.join(script_dir, "src", "main.py")
    
    # Run streamlit with the main file
    cmd = [sys.executable, "-m", "streamlit", "run", main_file] + sys.argv[1:]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
