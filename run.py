#!/usr/bin/env python3

import sys
import os
from streamlit.web import cli as stcli

def main():
    """
    Run the Streamlit application by directly invoking its command-line interface.
    This ensures that Streamlit's file watcher and hot-reloading work correctly.
    """
    # Get the directory of this script to build the full path to main.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_py_path = os.path.join(script_dir, "src", "main.py")

    # To run Streamlit programmatically, we need to manipulate sys.argv
    # to mimic the command line arguments: `streamlit run src/main.py`
    sys.argv = [
        "streamlit",
        "run",
        main_py_path,
        # You can add other streamlit arguments here if needed, e.g.:
        # "--server.port", "8502"
    ]

    # Call Streamlit's main entry point
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()