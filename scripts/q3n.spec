# scripts/q3n.spec
from pathlib import Path

block_cipher = None
repo_root = Path(SPECPATH).parent  # SPECPATH is scripts/, so parent is repo root

a = Analysis(
    [str(repo_root / 'gui' / 'app.py')],
    pathex=[str(repo_root)],
    binaries=[],
    datas=[
        (str(repo_root / 'core'), 'core'),
        (str(repo_root / 'gui'), 'gui'),
        (str(repo_root / 'app'), 'app'),
        (str(repo_root / 'art'), 'art'),
        (str(repo_root / 'examples'), 'examples'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'PySide6.QtUiTools',
        'PySide6.QtSvg',
        'PySide6.QtPrintSupport',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='q3n',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='q3n',
)
