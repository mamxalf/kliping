#!/usr/bin/env python3
"""Build script for Clipper CLI executable.

This script helps build the executable using PyInstaller.

Usage:
    python build.py              # Build for current platform
    python build.py --clean      # Clean build artifacts first
    python build.py --onefile    # Build as single executable file
    
Requirements:
    pip install pyinstaller
    
For Windows build:
    Run this script on a Windows machine or use GitHub Actions.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def clean_build_artifacts():
    """Remove build artifacts."""
    artifacts = ['build', 'dist', '__pycache__']
    spec_files = list(Path('.').glob('*.spec'))
    
    for artifact in artifacts:
        if Path(artifact).exists():
            print(f"Removing {artifact}/")
            shutil.rmtree(artifact)
    
    # Clean pycache in src
    for pycache in Path('src').rglob('__pycache__'):
        print(f"Removing {pycache}/")
        shutil.rmtree(pycache)
    
    print("[OK] Build artifacts cleaned")


def check_pyinstaller():
    """Check if PyInstaller is installed."""
    try:
        import PyInstaller
        print(f"[OK] PyInstaller version: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("[ERROR] PyInstaller not found. Install with: pip install pyinstaller")
        return False


def build_executable(onefile: bool = False, clean: bool = False):
    """Build the executable."""
    project_root = Path(__file__).parent
    
    if clean:
        clean_build_artifacts()
        print()
    
    if not check_pyinstaller():
        return False
    
    # Ensure we're in the project root
    os.chdir(project_root)
    
    print("\n[BUILD] Building Clipper CLI executable...\n")
    
    # Build command
    if onefile:
        # Single file executable (larger but easier to distribute)
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--onefile',
            '--console',
            '--name', 'clipper',
            '--paths', 'src',
            # Add hidden imports
            '--hidden-import', 'clipper_cli',
            '--hidden-import', 'clipper_cli.interactive',
            '--hidden-import', 'clipper_cli.interactive.app',
            '--hidden-import', 'clipper_cli.license',
            '--hidden-import', 'InquirerPy',
            '--hidden-import', 'rich',
            '--hidden-import', 'typer',
            '--hidden-import', 'pydantic',
            '--hidden-import', 'pydantic_settings',
            '--hidden-import', 'moviepy',
            '--hidden-import', 'imageio',
            '--hidden-import', 'imageio.core',
            '--hidden-import', 'imageio.plugins',
            '--hidden-import', 'imageio_ffmpeg',
            '--hidden-import', 'assemblyai',
            '--hidden-import', 'ollama',
            '--hidden-import', 'openai',
            '--hidden-import', 'anthropic',
            '--hidden-import', 'google.generativeai',
            # Collect data for imageio
            '--collect-data', 'imageio',
            '--collect-submodules', 'imageio',
            'src/clipper_cli/interactive/app.py',
        ]
    else:
        # Use spec file for more control
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            'clipper.spec',
        ]
    
    print(f"Running: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n[OK] Build successful!")
        
        if onefile:
            if sys.platform == 'win32':
                exe_path = project_root / 'dist' / 'clipper.exe'
            else:
                exe_path = project_root / 'dist' / 'clipper'
        else:
            if sys.platform == 'win32':
                exe_path = project_root / 'dist' / 'clipper' / 'clipper.exe'
            else:
                exe_path = project_root / 'dist' / 'clipper' / 'clipper'
        
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n[OUTPUT] Executable: {exe_path}")
            print(f"[INFO] Size: {size_mb:.1f} MB")
        
        return True
    else:
        print("\n[ERROR] Build failed!")
        return False


def main():
    parser = argparse.ArgumentParser(description="Build Clipper CLI executable")
    parser.add_argument(
        '--clean', '-c',
        action='store_true',
        help='Clean build artifacts before building'
    )
    parser.add_argument(
        '--onefile', '-o',
        action='store_true',
        help='Build as a single executable file'
    )
    parser.add_argument(
        '--clean-only',
        action='store_true',
        help='Only clean build artifacts, do not build'
    )
    
    args = parser.parse_args()
    
    if args.clean_only:
        clean_build_artifacts()
        return 0
    
    success = build_executable(onefile=args.onefile, clean=args.clean)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
