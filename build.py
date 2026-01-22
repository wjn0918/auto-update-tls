#!/usr/bin/env python3
"""
Build script to create executable from auto_certbot.py using PyInstaller
"""

import subprocess
import sys
import os

def build_executable():
    """Build executable using PyInstaller"""
    script_path = 'main.py'

    if not os.path.exists(script_path):
        print(f"Error: {script_path} not found")
        sys.exit(1)

    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--onefile',  # Create a single executable file
        '--name', 'auto-certbot',
        script_path
    ]

    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        print("Executable built successfully!")
        print("Find the executable in the 'dist' directory")
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    build_executable()
