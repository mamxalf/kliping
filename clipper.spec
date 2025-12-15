# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Clipper CLI.

Build command:
    pyinstaller clipper.spec

This will create:
    - dist/clipper/clipper.exe (Windows)
    - dist/clipper/clipper (macOS/Linux)
"""

import sys
from pathlib import Path

# Get the project root
project_root = Path(SPECPATH)
src_path = project_root / "src"

a = Analysis(
    [str(src_path / 'clipper_cli' / 'interactive' / 'app.py')],
    pathex=[str(src_path)],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Core modules
        'clipper_cli',
        'clipper_cli.main',
        'clipper_cli.config',
        'clipper_cli.models',
        'clipper_cli.license',
        
        # Interactive modules
        'clipper_cli.interactive',
        'clipper_cli.interactive.app',
        'clipper_cli.interactive.prompts',
        'clipper_cli.interactive.screens',
        
        # Video processing
        'clipper_cli.video',
        'clipper_cli.video.processor',
        'clipper_cli.video.clipper',
        
        # Transcription
        'clipper_cli.transcription',
        'clipper_cli.transcription.base',
        'clipper_cli.transcription.whisper_service',
        'clipper_cli.transcription.assemblyai_service',
        
        # LLM providers
        'clipper_cli.llm',
        'clipper_cli.llm.base',
        'clipper_cli.llm.factory',
        'clipper_cli.llm.ollama_provider',
        'clipper_cli.llm.openai_provider',
        'clipper_cli.llm.gemini_provider',
        'clipper_cli.llm.claude_provider',
        
        # Analysis
        'clipper_cli.analysis',
        'clipper_cli.analysis.viral_detector',
        'clipper_cli.analysis.prompts',
        
        # Batch processing
        'clipper_cli.batch',
        'clipper_cli.batch.processor',
        'clipper_cli.batch.reporter',
        
        # Utils
        'clipper_cli.utils',
        'clipper_cli.utils.console',
        
        # Third-party libraries
        'typer',
        'rich',
        'rich.console',
        'rich.panel',
        'rich.table',
        'rich.progress',
        'InquirerPy',
        'InquirerPy.prompts',
        'InquirerPy.base',
        'InquirerPy.validator',
        
        # Pydantic
        'pydantic',
        'pydantic_settings',
        
        # Video/Audio
        'moviepy',
        'moviepy.editor',
        
        # Whisper (if included - makes binary large)
        # Uncomment if you want to bundle whisper
        # 'whisper',
        # 'torch',
        
        # AssemblyAI
        'assemblyai',
        
        # LLM SDKs
        'ollama',
        'openai',
        'anthropic',
        'google.generativeai',
        
        # Other deps
        'aiofiles',
        'dotenv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy packages that aren't needed
        'matplotlib',
        'numpy.distutils',
        'scipy',
        'pandas',
        'PIL',
        'tkinter',
        'PyQt5',
        'PyQt6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='clipper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here: 'assets/icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='clipper',
)
